import React,{useId,useMemo,useRef,useState} from 'react';
import {ArrowRight,Compass,MapPin,Search,X} from 'lucide-react';
import districtData from './data/karnataka-districts.json';
import boundaries from './data/karnataka-boundaries.json';
import artworkBoundaries from './data/karnataka-artwork-boundaries.json';
import './district-explorer.css';

const text={
  kn:{eyebrow:'ನೆಲದ ನೆನಪುಗಳು',title:'ಒಂದು ನಾಡು. ಹಲವು ಕಥೆಗಳು.',intro:'ಕರ್ನಾಟಕದ ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಿ. ಅದರ ಪರಂಪರೆ, ಸಂಸ್ಕೃತಿ ಮತ್ತು ವಿಶೇಷತೆಗಳನ್ನು ತಿಳಿಯಿರಿ.',map:'ಕರ್ನಾಟಕದ ಜಿಲ್ಲೆಗಳ ನಕ್ಷೆ',choose:'ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಿ',search:'ಜಿಲ್ಲೆಯ ಹೆಸರನ್ನು ಹುಡುಕಿ',districts:'ಜಿಲ್ಲೆಗಳು',hint:'ನಕ್ಷೆಯ ಜಿಲ್ಲೆಯನ್ನು ಒತ್ತಿ ಅಥವಾ ಪಟ್ಟಿಯಿಂದ ಆಯ್ಕೆ ಮಾಡಿ.',about:'ಜಿಲ್ಲೆಯ ಪರಿಚಯ',highlights:'ಇಲ್ಲಿನ ವಿಶೇಷತೆಗಳು',history:'ಇತಿಹಾಸ',places:'ನೋಡಬೇಕಾದ ಸ್ಥಳಗಳು',food:'ಸ್ಥಳೀಯ ಆಹಾರ',culture:'ಕಲೆ ಮತ್ತು ಸಂಸ್ಕೃತಿ',close:'ವಿವರ ಮುಚ್ಚಿ',emptyTitle:'ನಿಮ್ಮ ಮುಂದಿನ ಕಥೆ ಎಲ್ಲಿಂದ?',empty:'ನಕ್ಷೆಯಲ್ಲಿ ಅಥವಾ ಪಟ್ಟಿಯಲ್ಲಿ ಒಂದು ಜಿಲ್ಲೆಯನ್ನು ಆಯ್ಕೆ ಮಾಡಿ.',noResults:'ಈ ಹೆಸರಿನ ಜಿಲ್ಲೆ ಕಂಡುಬಂದಿಲ್ಲ.',source:'ಮಾಹಿತಿ: ನೀವು ನೀಡಿದ ಜಿಲ್ಲಾ ಪರಿಚಯ ದಾಖಲೆ',mapNote:'ಪರಿಚಯಕ್ಕಾಗಿ ನೀಡಿದ ಗಡಿ ನಕ್ಷೆ',credit:'ನಕ್ಷೆಯ ಮೂಲ ಮತ್ತು ಪರವಾನಗಿ',selected:'ಆಯ್ದ ಜಿಲ್ಲೆ',all:'ಎಲ್ಲ ಜಿಲ್ಲೆಗಳು',photo:'ಚಿತ್ರ ಲಭ್ಯವಿಲ್ಲ',read:'ಜಿಲ್ಲೆಯ ವಿವರಕ್ಕೆ ಹೋಗಿ'},
  en:{eyebrow:'STORIES OF THE LAND',title:'One state. Many stories.',intro:'Choose a district of Karnataka to discover its heritage, culture and distinctive places.',map:'District map of Karnataka',choose:'Choose a district',search:'Search district names',districts:'districts',hint:'Select a district on the map or choose one from the list.',about:'About the district',highlights:'Known for',history:'History',places:'Places to visit',food:'Local food',culture:'Arts & culture',close:'Close district details',emptyTitle:'Where will your next story begin?',empty:'Choose a district on the map or in the list.',noResults:'No district matches that name.',source:'Information: your supplied district reference document',mapNote:'Illustrative district boundary map',credit:'Map source & licence',selected:'Selected district',all:'All districts',photo:'Image unavailable',read:'Go to district details'}
};

function ContentSection({title,value}){
  if(Array.isArray(value))return value.length?<section className="district-section"><h3>{title}</h3><ul>{value.map((item,i)=><li key={i}>{item}</li>)}</ul></section>:null;
  return value?<section className="district-section"><h3>{title}</h3><p>{value}</p></section>:null;
}

export default function DistrictExplorer({districts=districtData,geometry=boundaries}){
  const [language,setLanguage]=useState('kn');
  const [mapView,setMapView]=useState('artwork');
  const clipPrefix='district-art-'+useId().replace(/[^a-zA-Z0-9_-]/g,'');
  const [selectedId,setSelectedId]=useState(districts.find(d=>d.id==='mysuru')?.id||districts[0]?.id||null);
  const [query,setQuery]=useState('');
  const [hovered,setHovered]=useState(null);
  const [failedImages,setFailedImages]=useState({});
  const panel=useRef(null);
  const t=text[language];
  const byCode=useMemo(()=>Object.fromEntries(districts.map(d=>[d.code,d])),[districts]);
  const selected=districts.find(d=>d.id===selectedId);
  const artwork=mapView==='artwork';
  const hoveredDistrict=districts.find(d=>d.id===hovered);
  const activeGeometry=artwork?artworkBoundaries:geometry;
  const hoveredShape=activeGeometry.paths.find(p=>p.code===hoveredDistrict?.code);
  const artworkImage='/images/karnataka-art-map.png';
  const visible=districts.filter(d=>[d.name.kn,d.name.en,...(d.aliases||[])].some(name=>name.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase())));
  function choose(district){setSelectedId(district.id);if(matchMedia('(max-width: 900px)').matches)requestAnimationFrame(showDetails);}
  function showDetails(){panel.current?.scrollIntoView({behavior:matchMedia('(prefers-reduced-motion: reduce)').matches?'auto':'smooth',block:'start'});panel.current?.focus({preventScroll:true});}
  return <section className="district-explorer" lang={language} aria-labelledby="district-page-title">
    <div className="district-page-heading">
      <div><span className="district-eyebrow"><Compass size={17}/>{t.eyebrow}</span><h1 id="district-page-title">{t.title}</h1><p>{t.intro}</p></div>
      <div className="district-language" role="group" aria-label="District information language">
        <button type="button" aria-label="Show district information in Kannada" aria-pressed={language==='kn'} onClick={()=>setLanguage('kn')}>ಕನ್ನಡ</button>
        <button type="button" aria-label="Show district information in English" aria-pressed={language==='en'} onClick={()=>setLanguage('en')}>English</button>
      </div>
    </div>
    <div className="district-layout">
      <div className="district-map-column">
        <div className="district-map-panel">
          <div className="district-map-top"><span><MapPin size={16}/>{t.map}</span><span className="district-count">{districts.length} {t.districts}</span></div>
          <div className="district-map-switch" role="group" aria-label="Map view">
            <button type="button" aria-label="Show illustrated Karnataka map" aria-pressed={artwork} onClick={()=>{setMapView('artwork');setHovered(null);}}>{language==='kn'?'ಚಿತ್ರ ನಕ್ಷೆ':'Illustrated map'}</button>
            <button type="button" aria-label="Show previous district boundary map" aria-pressed={!artwork} onClick={()=>{setMapView('boundaries');setHovered(null);}}>{language==='kn'?'ಹಿಂದಿನ ನಕ್ಷೆ':'Previous map'}</button>
          </div>
          <label className="district-mobile-select">{t.choose}<select aria-label={t.choose} value={selectedId||''} onChange={e=>{const district=districts.find(d=>d.id===e.target.value);if(district)choose(district);else setSelectedId(null);}}><option value="">{t.choose}</option>{districts.map(d=><option key={d.id} value={d.id}>{d.name[language]}</option>)}</select></label>
          <div className={'district-map-stage'+(artwork?' district-artwork-stage':'')}>
            <svg className={'district-map-svg'+(artwork?' district-artwork-svg':'')} viewBox={activeGeometry.viewBox} aria-label={t.map} role="group">
              {artwork&&<>
                <defs>{artworkBoundaries.paths.map(shape=><clipPath key={shape.code} id={clipPrefix+'-'+shape.code} clipPathUnits="userSpaceOnUse"><path d={shape.d}/></clipPath>)}</defs>
                <image className="district-artwork-image" href={artworkImage} x="0" y="0" width={artworkBoundaries.width} height={artworkBoundaries.height} preserveAspectRatio="xMidYMid meet" aria-hidden="true"/>
              </>}
              {activeGeometry.paths.map(shape=>{
                const district=byCode[shape.code];if(!district)return null;
                const active=district.id===selectedId;
                return <path key={shape.code} d={shape.d} data-district={district.id} role="button" tabIndex={0} aria-label={district.name[language]} aria-pressed={active} className={'district-shape'+(artwork?' district-artwork-region':'')+(active?' is-selected':'')} onClick={()=>choose(district)} onMouseEnter={()=>setHovered(district.id)} onMouseLeave={()=>setHovered(null)} onFocus={()=>setHovered(district.id)} onBlur={()=>setHovered(null)} onKeyDown={e=>{if(e.key==='Enter'||e.key===' '){e.preventDefault();choose(district);}}}><title>{district.name[language]}</title></path>;
              })}
              {artwork&&hoveredShape&&<g key={hoveredShape.code} className="district-artwork-lift" style={{transformOrigin:(hoveredShape.center?.[0]||500)+'px '+(hoveredShape.center?.[1]||700)+'px'}} aria-hidden="true" pointerEvents="none">
                <g clipPath={'url(#'+clipPrefix+'-'+hoveredShape.code+')'}><image href={artworkImage} x="0" y="0" width={artworkBoundaries.width} height={artworkBoundaries.height} preserveAspectRatio="xMidYMid meet"/></g>
                <path d={hoveredShape.d} className="district-artwork-lift-outline"/>
              </g>}
            </svg>
            {!artwork&&<><span className="district-north" aria-hidden="true">N<span>↑</span></span>
            <span className="district-sea" aria-hidden="true">{language==='kn'?'ಅರಬ್ಬೀ ಸಮುದ್ರ':'ARABIAN SEA'}</span></>}
          </div>
          <div className="district-map-selection" role="status"><MapPin size={18}/><strong>{districts.find(d=>d.id===hovered)?.name[language]||selected?.name[language]||t.choose}</strong>{selected&&<button type="button" className="district-details-jump" aria-label={t.read} onClick={showDetails}><ArrowRight size={20}/></button>}</div>
          <p className="district-map-hint">{t.hint}{artwork&&<span className="district-artwork-note">{language==='kn'?'ಕಲಾತ್ಮಕ ಚಿತ್ರ; ಜಿಲ್ಲೆಯ ಗಡಿಗಳಿಗೆ ಹಿಂದಿನ ನಕ್ಷೆ ನೋಡಿ.':'Artistic illustration; use the previous map to view district boundaries.'}</span>}</p>
          <div className="district-legend"><span><i/>{t.all}</span><span><i className="active"/>{t.selected}</span></div>
        </div>
        <div className="district-picker-panel">
          <label className="district-search"><Search size={18}/><input aria-label={t.search} placeholder={t.search} value={query} onChange={e=>setQuery(e.target.value)}/>{query&&<button type="button" aria-label={language==='kn'?'ಹುಡುಕಾಟ ತೆರವುಗೊಳಿಸಿ':'Clear district search'} onClick={()=>setQuery('')}><X size={16}/></button>}</label>

          <div className="district-list" aria-label={t.choose}>{visible.map((d,i)=><button type="button" key={d.id} aria-pressed={d.id===selectedId} onClick={()=>choose(d)}><span className="district-list-dot"/>{d.name[language]}{d.id===selectedId&&<ArrowRight size={14}/>}</button>)}</div>
          {!visible.length&&<p className="district-no-results" role="status">{t.noResults}</p>}
        </div>
      </div>
      <aside ref={panel} tabIndex={-1} className="district-info" aria-label={selected?.name[language]||t.choose}>
        {selected?<>
          <div className="district-photo-wrap">{selected.image?.src&&!failedImages[selected.id]?<img className="district-photo" src={selected.image.src} alt={selected.image.alt?.[language]||selected.name[language]} style={{objectPosition:selected.image.position||'center'}} width="900" height="600" onError={()=>setFailedImages(old=>({...old,[selected.id]:true}))}/>:<div className="district-photo-fallback"><MapPin size={40}/><span>{t.photo}</span></div>}<button type="button" className="district-close" aria-label={t.close} onClick={()=>setSelectedId(null)}><X size={19}/></button><span className="district-photo-tag">{String(districts.indexOf(selected)+1).padStart(2,'0')} / {districts.length}</span></div>
          <div className="district-info-body" key={selected.id}>
            <div className="district-card-kicker"><span className="district-eyebrow">{language==='kn'?'ನಮ್ಮ ಕರ್ನಾಟಕ':'OUR KARNATAKA'}</span><MapPin size={20}/></div>
            <h2>{selected.name[language]}</h2>
            {selected.aliases?.length>0&&<p className="district-alias">{language==='kn'?'ಹಿಂದಿನ ಹೆಸರು: ರಾಮನಗರ':'Formerly Ramanagara'}</p>}
            <ContentSection title={t.about} value={selected.description?.[language]}/>
            <ContentSection title={t.highlights} value={selected.highlights?.[language]}/>
            <ContentSection title={t.history} value={selected.history?.[language]}/>
            <ContentSection title={t.places} value={selected.places?.[language]}/>
            <ContentSection title={t.food} value={selected.food?.[language]}/>
            <ContentSection title={t.culture} value={selected.culture?.[language]}/>
            <p className="district-content-source">{t.source}</p>
          </div>
        </>:<div className="district-empty"><Compass size={52}/><h2>{t.emptyTitle}</h2><p>{t.empty}</p></div>}
      </aside>
    </div>
    <div className="district-map-attribution"><span>{t.mapNote}</span><details><summary>{t.credit}</summary><p><a href={geometry.source} target="_blank" rel="noreferrer">{geometry.author}</a> · <a href={geometry.licenseUrl} target="_blank" rel="noreferrer">{geometry.license}</a>. {language==='kn'?'ಗಡಿಯ ಆಕಾರಗಳನ್ನು ಪ್ರತ್ಯೇಕಿಸಿ ಬಣ್ಣ ಮತ್ತು ಸಂವಹನ ಸೇರಿಸಲಾಗಿದೆ.':'Adapted: district shapes extracted, recoloured, and made interactive.'}</p></details></div>
  </section>;
}
