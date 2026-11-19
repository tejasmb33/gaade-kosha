import React from 'react';
import {displayText} from './displayText';
import './proverb-information.css';
export default function ProverbInformation({row,titleLevel='h3',titleRef=null}){
 const tr=row.translation?.fields||{},d=row.display,Title=titleLevel;
 const english=d?.proverb_en??tr.proverb_en;
 const meaningKn=d?.contextual_meaning_kn??tr.contextual_meaning_kn;
 const example=d?.example||{kn:tr.example_usage_kn||(/[\u0c80-\u0cff]/.test(row.example_usage||'')?row.example_usage:''),en:/[\u0c80-\u0cff]/.test(row.example_usage||'')?'':row.example_usage};
 const scenarios=d?.situations||row.situations?.map(s=>({[s.language]:s.text}))||[];
 const text=(value,lang)=>row.__writing&&!value?null:<p lang={lang}>{displayText(value||'')||(lang==='kn'?'ಮಾಹಿತಿ ಲಭ್ಯವಿಲ್ಲ':'Information unavailable')}</p>;
 return <div className="proverb-information">
  <span className="eyebrow" lang="kn">ಕನ್ನಡ ಗಾದೆ · Kannada proverb</span><Title ref={titleRef} tabIndex={titleRef?-1:undefined} lang="kn">{row.proverb_kn}</Title>
  <dl>
   <dt>ಇಂಗ್ಲಿಷ್ ಸಮಾನಾರ್ಥ · English equivalent</dt><dd>{text(english,'en')}</dd>
   <dt>ಕನ್ನಡ ಅರ್ಥ · Kannada meaning</dt><dd>{text(meaningKn,'kn')}</dd>
   <dt>ಇಂಗ್ಲಿಷ್ ಅರ್ಥ · English meaning</dt><dd>{text(row.contextual_meaning,'en')}</dd>
   <dt>ಉದಾಹರಣೆ · Example</dt><dd>{text(example.kn,'kn')}{text(example.en,'en')}</dd>
   <dt>ಪ್ರದೇಶ · Region</dt><dd>{row.region?<>{text(tr.region_kn||row.region,'kn')}{text(row.region,'en')}</>:<><p lang="kn">ಕರ್ನಾಟಕ — ನಿರ್ದಿಷ್ಟ ಪ್ರದೇಶ ದೃಢಪಟ್ಟಿಲ್ಲ</p><p lang="en">Karnataka — specific region unverified</p></>}</dd>
   {[0,1].map(i=><React.Fragment key={i}><dt>ಸಂದರ್ಭ {i+1} · Situation {i+1}</dt><dd>{text(scenarios[i]?.kn,'kn')}{text(scenarios[i]?.en,'en')}</dd></React.Fragment>)}
  </dl>
 </div>;
}
