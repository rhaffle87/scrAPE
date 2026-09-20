"""Asynchronous background ML pipeline worker for non-blocking aesthetic scoring, tagging, and cropping."""

from __future__ import annotations

import logging
from pathlib import Path
import queue
import threading
from typing import Any, Callable

from core.models import ImageItem
from ml.aesthetic_scorer import AestheticScorer
from ml.dataset_cropper import DatasetCropper
from ml.dataset_tagger import DatasetTagger

LOGGER = logging.getLogger(__name__)


class AsyncMLPipelineWorker(threading.Thread):
    """
    Decoupled background worker that consumes downloaded images from an ingest queue,
    applying aesthetic quality scoring, smart face/content cropping, and dataset auto-tagging
    asynchronously without blocking network crawling throughput.
    """

    def __init__(
        self,
        ingest_queue: queue.Queue | None = None,
        min_aesthetic_score: float | None = None,
        auto_crop: bool = False,
        auto_tag: bool = False,
        cull_rejected: bool = True,
        on_item_processed: Callable[[ImageItem], None] | None = None,
        on_item_culled: Callable[[ImageItem, str], None] | None = None,
    ):
        super().__init__(daemon=True, name="AsyncMLPipelineWorker")
        self.ingest_queue: queue.Queue = ingest_queue or queue.Queue()
        self.min_aesthetic_score = min_aesthetic_score
        self.auto_crop = auto_crop
        self.auto_tag = auto_tag
        self.cull_rejected = cull_rejected

        self.on_item_processed = on_item_processed
        self.on_item_culled = on_item_culled

        self._stop_event = threading.Event()
        self._processed_count = 0
        self._culled_count = 0

        # Lazy-loaded ML models
        self._aesthetic_scorer: AestheticScorer | None = None
        self._cropper: DatasetCropper | None = None
        self._tagger: DatasetTagger | None = None

    @property
    def aesthetic_scorer(self) -> AestheticScorer:
        if self._aesthetic_scorer is None:
            self._aesthetic_scorer = AestheticScorer()
        return self._aesthetic_scorer

    @property
    def cropper(self) -> DatasetCropper:
        if self._cropper is None:
            self._cropper = DatasetCropper()
        return self._cropper

    @property
    def tagger(self) -> DatasetTagger:
        if self._tagger is None:
            self._tagger = DatasetTagger(use_vision_model=True)
        return self._tagger

    def enqueue(self, item: ImageItem, file_path: str | Path) -> None:
        """Enqueue an asset for background ML enrichment."""
        self.ingest_queue.put((item, str(file_path)))

    def stop(self) -> None:
        """Signal worker to stop after queue is drained."""
        self._stop_event.set()

    def run(self) -> None:
        """Main consumer loop."""
        LOGGER.info(
            "AsyncMLPipelineWorker started (min_score=%s, auto_crop=%s, auto_tag=%s)",
            self.min_aesthetic_score,
            self.auto_crop,
            self.auto_tag,
        )

        while not (self._stop_event.is_set() and self.ingest_queue.empty()):
            try:
                task = self.ingest_queue.get(timeout=0.5)
            except queue.Empty:
                continue

            if task is None:  # Poison pill
                self.ingest_queue.task_done()
                break

            item, path_str = task
            try:
                self._process_item(item, path_str)
            except (KeyboardInterrupt, SystemExit):
                raise
            except Exception as exc:
                LOGGER.warning("ML worker failed on asset %s: %s", path_str, exc)
            finally:
                self.ingest_queue.task_done()

        LOGGER.info(
            "AsyncMLPipelineWorker stopped. Processed %d, culled %d items.",
            self._processed_count,
            self._culled_count,
        )

    def _process_item(self, item: ImageItem, path_str: str) -> None:
        p = Path(path_str)
        if not p.exists() or not p.is_file():
            return

        from PIL import Image

        try:
            with Image.open(p) as img:
                img.load()  # verify valid image
        except Exception:
            return

        # 1. Aesthetic Quality Scoring & Optional Culling
        score: float | None = None
        if self.min_aesthetic_score is not None:
            try:
                score = self.aesthetic_scorer.score_image(p)
                item.aesthetic_score = score
                if score < self.min_aesthetic_score:
                    LOGGER.info(
                        "Culling low aesthetic asset (score %.2f < %.2f): %s",
                        score,
                        self.min_aesthetic_score,
                        p.name,
                    )
                    item.status = "rejected"
                    item.failure_reason = f"low_aesthetic_score_{score:.1f}"
                    self._culled_count += 1
                    if self.cull_rejected:
                        try:
                            p.unlink(missing_ok=True)
                        except Exception:
                            pass
                    if self.on_item_culled:
                        self.on_item_culled(item, f"low_aesthetic_score_{score:.1f}")
                    return
            except Exception as e:
                LOGGER.warning("Aesthetic scoring error on %s: %s", p.name, e)

        # 2. Smart Face / Content Aspect Cropping
        if self.auto_crop:
            try:
                crop_dir = p.parent / "cropped"
                crop_dir.mkdir(parents=True, exist_ok=True)
                crop_path = crop_dir / f"crop_{p.name}"

                with Image.open(p) as src_img:
                    cropped_img = self.cropper.crop_image(src_img)
                    cropped_img.save(crop_path)
                    item.crop_box = {"width": cropped_img.width, "height": cropped_img.height}
            except Exception as e:
                LOGGER.warning("Auto-crop error on %s: %s", p.name, e)

        # 3. WD14 Booru Dataset Tagging
        if self.auto_tag:
            try:
                tags = self.tagger.tag_image(p)
                item.tags = tags
                # Write sidecar .txt file next to original image
                sidecar_path = p.with_suffix(".txt")
                if tags:
                    sidecar_path.write_text(", ".join(tags), encoding="utf-8")
            except Exception as e:
                LOGGER.warning("Auto-tagging error on %s: %s", p.name, e)

        self._processed_count += 1
        if self.on_item_processed:
            self.on_item_processed(item)

    def join_and_finish(self, timeout: float = 30.0) -> None:
        """Signal stop, wait for queue drain, and join thread."""
        self.stop()
        self.join(timeout=timeout)

    def stats(self) -> dict[str, Any]:
        return {
            "processed_count": self._processed_count,
            "culled_count": self._culled_count,
            "queue_depth": self.ingest_queue.qsize(),
        }
