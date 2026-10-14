const fs = require('fs');
const code = fs.readFileSync('docs/site/i18n.js', 'utf8');
const dictPart = code.split('function setPortalLanguage')[0];
eval(dictPart.replace('const I18N_DICTS', 'global.I18N_DICTS'));

console.log('Languages in I18N_DICTS:', Object.keys(global.I18N_DICTS));
for (const lang of Object.keys(global.I18N_DICTS)) {
  const d = global.I18N_DICTS[lang];
  console.log(lang, {
    modules: d.modules ? d.modules.length : 0,
    nav: d.nav ? Object.keys(d.nav).length : 0,
    sections: d.sections ? Object.keys(d.sections).length : 0
  });
}
