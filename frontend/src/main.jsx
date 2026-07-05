import React, { useEffect, useMemo, useRef, useState } from 'react';
import { createRoot } from 'react-dom/client';
import {
  ArrowUp, Award, BookOpen, CarFront, Check, CheckCircle2, ChevronLeft, ChevronRight,
  Clock3, CornerUpRight, Crosshair, Flag, Gauge, Heart, Home, Layers, LocateFixed, MapPin, MessageCircle, Navigation,
  Play, RotateCcw, Route, Search, ShieldCheck, SlidersHorizontal, Sparkles,
  Star, Target, ThumbsDown, ThumbsUp, Trophy, Volume2, X, Zap
} from 'lucide-react';
import './styles.css';

const API='/api';
const CHARACTER='/static/api/orai_character.png';
const DEFAULT_ZONE={zone_name:'삼성 멀티캠퍼스 역삼',address:'서울 강남구 테헤란로 212',latitude:37.501327,longitude:127.039623};
const DEFAULT_COORDS=[
  {lat:37.501327,lng:127.039623},{lat:37.500658,lng:127.036430},
  {lat:37.502688,lng:127.030260},{lat:37.50512,lng:127.03445},{lat:37.501327,lng:127.039623},
];
const cls=(...xs)=>xs.filter(Boolean).join(' ');

async function api(path, options={}){
  const response=await fetch(`${API}${path}`,{headers:{'Content-Type':'application/json',...(options.headers||{})},...options});
  const data=await response.json().catch(()=>({}));
  if(!response.ok) throw new Error(data.message||'요청을 처리하지 못했습니다.');
  return data;
}

function useKakaoMap(coords,zone){
  const ref=useRef(null); const map=useRef(null); const polyline=useRef(null); const markers=useRef([]);
  const [ready,setReady]=useState(false); const [message,setMessage]=useState('지도 준비 중');
  useEffect(()=>{
    const key=window.ORAI_CONFIG?.kakaoJsKey||'';
    if(!key){setMessage('지도 키 없이 오프라인 미리보기로 표시 중');return;}
    const init=()=>{
      try{
        map.current=new window.kakao.maps.Map(ref.current,{center:new window.kakao.maps.LatLng(DEFAULT_ZONE.latitude,DEFAULT_ZONE.longitude),level:5});
        setReady(true);setMessage('');
      }catch(e){setMessage('지도를 불러오지 못해 미리보기로 표시 중');}
    };
    if(window.kakao?.maps){window.kakao.maps.load(init);return;}
    const script=document.createElement('script');
    script.src=`https://dapi.kakao.com/v2/maps/sdk.js?appkey=${key}&autoload=false`;
    script.async=true;script.onload=()=>window.kakao?.maps?.load(init);script.onerror=()=>setMessage('지도 연결에 실패해 미리보기로 표시 중');
    document.head.appendChild(script);
  },[]);
  useEffect(()=>{
    if(!ready||!map.current)return;
    const points=(coords?.length?coords:DEFAULT_COORDS).map(p=>new window.kakao.maps.LatLng(p.lat,p.lng));
    markers.current.forEach(m=>m.setMap(null)); markers.current=[];
    if(polyline.current)polyline.current.setMap(null);
    polyline.current=new window.kakao.maps.Polyline({path:points,strokeWeight:7,strokeColor:'#F34B5C',strokeOpacity:.95,strokeStyle:'solid'});
    polyline.current.setMap(map.current);
    const bounds=new window.kakao.maps.LatLngBounds();points.forEach((p,i)=>{bounds.extend(p);if(i===0||i===points.length-1||i===Math.floor(points.length/2)){markers.current.push(new window.kakao.maps.Marker({map:map.current,position:p}));}});
    map.current.setBounds(bounds);
  },[ready,coords]);
  useEffect(()=>{if(ready&&zone&&!coords?.length)map.current.setCenter(new window.kakao.maps.LatLng(zone.latitude,zone.longitude));},[ready,zone,coords]);
  return {ref,ready,message};
}

function RouteFallback({coords}){
  const points=coords?.length?coords:DEFAULT_COORDS;
  const minLat=Math.min(...points.map(p=>p.lat)),maxLat=Math.max(...points.map(p=>p.lat));
  const minLng=Math.min(...points.map(p=>p.lng)),maxLng=Math.max(...points.map(p=>p.lng));
  const xy=points.map(p=>({x:12+76*((p.lng-minLng)/(maxLng-minLng||1)),y:86-72*((p.lat-minLat)/(maxLat-minLat||1))}));
  return <div className="fallback-map">
    <div className="map-grid"/><i className="map-road road-one"/><i className="map-road road-two"/><i className="map-road road-three"/>
    <svg viewBox="0 0 100 100" preserveAspectRatio="none"><polyline points={xy.map(p=>`${p.x},${p.y}`).join(' ')} fill="none" stroke="#F34B5C" strokeWidth="3.2" strokeLinecap="round" strokeLinejoin="round"/></svg>
    {xy.map((p,i)=><i key={i} className={cls('pin',i===0&&'start-pin')} style={{left:`${p.x}%`,top:`${p.y}%`}}>{i===0?<Flag size={11}/>:null}</i>)}
    <span className="road-name road-name-a">테헤란로</span><span className="road-name road-name-b">역삼역</span><span className="road-name road-name-c">강남대로</span>
  </div>
}

function MapStage({coords,zone,active}){
  const {ref,ready,message}=useKakaoMap(coords,zone);
  return <section className="map-stage">
    <div className="kakao-map" ref={ref}/>{!ready&&<RouteFallback coords={coords}/>} 
    <div className="map-search-card"><Search size={18}/><div><b>{zone?.zone_name||DEFAULT_ZONE.zone_name}</b><small>{zone?.address||DEFAULT_ZONE.address}</small></div><button aria-label="현재 위치"><LocateFixed size={18}/></button></div>
    <div className="map-state"><i/><span>{message||'실시간 지도 연결됨'}</span></div>
    <div className="map-legend"><span><i className="legend-dot zone"/>오라이존</span><span><i className="legend-dot route"/>연습 경로</span></div>
    {active&&<div className="driving-badge"><i/><b>주행 중</b><span>{active.course_name}</span></div>}
  </section>
}

function useNavigationProgress(routeCoords=[]){
  const [routeIndex,setRouteIndex]=useState(0); const [gpsState,setGpsState]=useState('GPS 연결 중');
  useEffect(()=>{
    if(!routeCoords.length)return;
    let watchId=null; let demoTimer=null; let gotGps=false;
    const nearestIndex=(lat,lng)=>{let best=0,bestDistance=Infinity;routeCoords.forEach((p,i)=>{const d=(p.lat-lat)**2+(p.lng-lng)**2;if(d<bestDistance){best=i;bestDistance=d;}});return best;};
    if(navigator.geolocation){
      watchId=navigator.geolocation.watchPosition(pos=>{gotGps=true;setGpsState('GPS 연결됨');setRouteIndex(nearestIndex(pos.coords.latitude,pos.coords.longitude));},()=>setGpsState('GPS 미수신 · 데모 진행'),{enableHighAccuracy:true,maximumAge:3000,timeout:7000});
    }else setGpsState('GPS 미지원 · 데모 진행');
    demoTimer=setInterval(()=>{if(!gotGps)setRouteIndex(i=>Math.min(routeCoords.length-1,i+Math.max(1,Math.floor(routeCoords.length/18))));},4200);
    return ()=>{if(watchId!==null&&navigator.geolocation)navigator.geolocation.clearWatch(watchId);if(demoTimer)clearInterval(demoTimer);};
  },[routeCoords]);
  return {routeIndex,gpsState};
}

function NavigationScreen({active,zone,onExit,onFinish}){
  const coords=active?.route_coords?.length?active.route_coords:DEFAULT_COORDS;
  const instructions=active?.navigation_instructions?.length?active.navigation_instructions:[
    {index:0,distance_m:120,description:'출발지에서 천천히 직진하세요.',turn_type:0},
    {index:Math.max(1,Math.floor(coords.length/2)),distance_m:180,description:'교차로 진입 전 보행자와 신호를 확인하세요.',turn_type:12},
    {index:Math.max(2,coords.length-1),distance_m:0,description:'목적지에 도착했습니다. 안전한 곳에 정차하세요.',turn_type:201},
  ];
  const {routeIndex,gpsState}=useNavigationProgress(coords);
  const {ref,ready,message}=useKakaoMap(coords,zone);
  const pct=Math.min(100,Math.round((routeIndex/Math.max(1,coords.length-1))*100));
  const next=instructions.find(item=>item.index>=routeIndex)||instructions[instructions.length-1];
  const remain=Math.max(0,Math.round((active?.distance_km||2.8)*(1-pct/100)*10)/10);
  const remainMinutes=Math.max(1,Math.ceil((active?.duration_minutes||active?.estimated_minutes||30)*(1-pct/100)));
  const turnIcon=next?.turn_type===12?<CornerUpRight size={39}/>:<ArrowUp size={42}/>;
  const current=coords[Math.min(routeIndex,coords.length-1)]||coords[0];
  const minLat=Math.min(...coords.map(p=>p.lat)),maxLat=Math.max(...coords.map(p=>p.lat));
  const minLng=Math.min(...coords.map(p=>p.lng)),maxLng=Math.max(...coords.map(p=>p.lng));
  const carX=12+76*((current.lng-minLng)/(maxLng-minLng||1)); const carY=86-72*((current.lat-minLat)/(maxLat-minLat||1));
  return <main className="navigation-screen">
    <section className="nav-map-wrap"><div className="kakao-map" ref={ref}/>{!ready&&<RouteFallback coords={coords}/>} {!ready&&<div className="nav-car-marker" style={{left:`${carX}%`,top:`${carY}%`}}><Navigation size={18}/></div>}
      <div className="nav-top-actions"><button onClick={onExit} aria-label="내비게이션 종료"><ChevronLeft/></button><div><b>초보운전 연습 주행</b><small>{message||gpsState}</small></div><button aria-label="음성 안내"><Volume2/></button></div>
      <div className="nav-instruction"><div className="nav-turn-icon">{turnIcon}</div><div><strong>{next?.distance_m||0}m</strong><h1>{next?.description||'안전하게 직진하세요.'}</h1><p>급하게 차선을 바꾸지 말고 주변 차량을 확인하세요.</p></div></div>
      <div className="nav-map-tools"><button><Crosshair/></button><button><Layers/></button></div>
      <div className="nav-speed"><small>현재 속도</small><b>32</b><span>km/h</span></div>
      <div className="nav-limit"><small>제한</small><b>50</b></div>
    </section>
    <section className="nav-bottom-sheet"><div className="nav-progress"><i style={{width:`${pct}%`}}/></div><div className="nav-route-summary"><div><span>남은 거리</span><b>{remain} km</b></div><div><span>예상 도착</span><b>{remainMinutes}분 후</b></div><div><span>진행률</span><b>{pct}%</b></div></div><div className="nav-course-row"><div className="nav-course-icon"><Gauge/></div><div><small>연습 중인 코스</small><b>{active.course_name}</b><span>{gpsState} · 운전 중 화면 조작 금지</span></div><button onClick={onFinish}>주행 종료</button></div></section>
  </main>
}

function Brand(){return <div className="brand"><div className="brand-symbol"><CarFront size={21}/></div><div><b>오라이</b><small>초보운전 레벨업 코치</small></div></div>}
const NAV=[['home','추천',Home],['mission','미션',Target],['history','기록',BookOpen],['community','커뮤니티',MessageCircle]];
function BottomNav({tab,setTab}){return <nav className="bottom-nav">{NAV.map(([id,label,Icon])=><button key={id} className={cls(tab===id&&'active')} onClick={()=>setTab(id)}><span><Icon size={20}/></span><small>{label}</small></button>)}</nav>}
function SideNav({tab,setTab,profile}){return <aside className="side-nav"><Brand/><div className="side-profile"><img src={CHARACTER}/><div><small>오늘도 안전운전</small><b>{profile?.nickname||'초보운전자 민지'}</b><em>Lv.{profile?.level||1} · {profile?.level_title||'새싹 드라이버'}</em></div></div><div className="side-links">{NAV.map(([id,label,Icon])=><button key={id} className={cls(tab===id&&'active')} onClick={()=>setTab(id)}><Icon size={18}/><span>{label}</span><ChevronRight size={15}/></button>)}</div><div className="safety-note"><ShieldCheck size={19}/><b>안전 안내</b><p>운전 중에는 화면을 조작하지 말고 안전한 곳에서 정차한 뒤 확인해 주세요.</p></div></aside>}

function LevelMini({profile}){const xp=profile?.xp||0,next=profile?.next_level_xp||500,pct=Math.min(100,(xp/next)*100);return <section className="level-mini"><div><span>MY DRIVING LEVEL</span><h3>Lv.{profile?.level||1} {profile?.level_title||'새싹 드라이버'}</h3></div><div className="level-ring"><Trophy size={16}/></div><div className="xp-track"><i style={{width:`${pct}%`}}/></div><small>{xp} XP <b>·</b> 다음 레벨까지 {Math.max(0,next-xp)} XP</small></section>}

function Chip({active,children,onClick}){return <button className={cls('chip',active&&'active')} onClick={onClick}>{children}</button>}
function FilterSheet({filters,setFilters,onRecommend,zones,loading}){
  return <section className="filter-sheet app-card"><div className="sheet-title"><div><span>ROUTE COACH</span><h2>오늘은 어떤 운전을<br/>연습할까요?</h2></div><SlidersHorizontal size={19}/></div>
    <label className="zone-select"><MapPin size={17}/><select value={filters.zone_id} onChange={e=>setFilters({...filters,zone_id:e.target.value})}>{zones.map(z=><option key={z.zone_id} value={z.zone_id}>{z.zone_name}</option>)}</select><ChevronRight size={16}/></label>
    <div className="filter-group"><b>난이도</b><div>{[['beginner','입문'],['adapt','적응'],['challenge','도전']].map(([id,l])=><Chip key={id} active={filters.level===id} onClick={()=>setFilters({...filters,level:id})}>{l}</Chip>)}</div></div>
    <div className="filter-group"><b>집중 연습</b><div>{[['lane_keep','차선 유지'],['right_turn','우회전'],['left_turn','좌회전'],['parking','주차 진입'],['lane_change','차선 변경']].map(([id,l])=><Chip key={id} active={filters.practice_type===id} onClick={()=>setFilters({...filters,practice_type:id})}>{l}</Chip>)}</div></div>
    <div className="filter-group"><b>연습 시간</b><div>{[20,30,45,60].map(v=><Chip key={v} active={filters.minutes===v} onClick={()=>setFilters({...filters,minutes:v})}>{v}분</Chip>)}</div></div>
    <button className="primary" disabled={loading} onClick={onRecommend}><Sparkles size={17}/>{loading?'안전한 루트를 찾는 중…':'맞춤 루트 추천받기'}</button>
  </section>
}

function RouteCard({course,index,onPreview,onStart}){return <article className="route-card app-card"><div className="route-card-head"><span className="route-order">0{index+1}</span><div><h3>{course.course_name}</h3><p>{course.reason}</p></div><strong><Star size={13}/>{course.recommend_score}</strong></div><div className="route-tags"><span>{course.practice_type_label}</span><span>{course.level_label}</span><span>부담도 {course.burden_label}</span></div><div className="route-metrics"><div><Clock3/><b>{course.estimated_range?.[0]}~{course.estimated_range?.[1]}분</b><small>예상 시간</small></div><div><Route/><b>{course.distance_km}km</b><small>왕복 거리</small></div><div><RotateCcw/><b>{course.metrics?.right_turn_count||0}회</b><small>우회전</small></div><div><Zap/><b>{course.reward_text||'+XP'}</b><small>완주 보상</small></div></div><div className="route-actions"><button className="secondary" onClick={()=>onPreview(course)}><Navigation size={15}/>루트 미리보기</button><button className="start" onClick={()=>onStart(course)}><Play size={15}/>이 코스로 시작</button></div></article>}

function HomePage({data,filters,setFilters,courses,onRecommend,onPreview,onStart,loading,policy}){return <main className="home-page"><section className="home-left"><LevelMini profile={data.profile}/><FilterSheet filters={filters} setFilters={setFilters} onRecommend={onRecommend} zones={data.zones} loading={loading}/></section><section className="route-list"><div className="section-head"><div><span>PERSONAL ROUTES</span><h2>나를 위한 연습 코스</h2></div><small>{courses.length?`${courses.length}개의 안전 코스`:'조건을 선택해 주세요'}</small></div>{policy&&<p className="policy">{policy}</p>}{courses.length?courses.map((c,i)=><RouteCard key={c.course_id} course={c} index={i} onPreview={onPreview} onStart={onStart}/>):<div className="empty app-card"><img src={CHARACTER}/><h3>부담 없는 첫 코스를 찾아드릴게요</h3><p>난이도와 집중 연습 항목을 고르면<br/>초보운전자에게 맞는 왕복 코스를 추천합니다.</p></div>}</section></main>}

function PageTitle({label,title,description,Icon}){return <div className="page-title"><div><span>{label}</span><h1>{title}</h1><p>{description}</p></div><Icon size={25}/></div>}
function MissionPage({data}){return <main className="content-page"><PageTitle label="LEVEL UP" title="미션 레벨업" description="하나씩 완주하며 운전 자신감을 키워보세요." Icon={Award}/><div className="summary"><div className="app-card"><b>{data.profile?.total_xp||0}</b><small>누적 XP</small></div><div className="app-card"><b>{data.profile?.completed_drives||0}</b><small>완료 미션</small></div><div className="app-card"><b>{data.profile?.total_distance||0}</b><small>누적 km</small></div></div><div className="mission-grid">{data.missions.map((m,i)=><article className={cls('mission app-card',m.completed&&'done')} key={m.course_id}><div className="mission-no">{m.completed?<Check/>:i+1}</div><div><div className="route-tags"><span>{m.practice_type_label}</span><span>{m.level_label}</span></div><h3>{m.course_name}</h3><p>{m.description}</p><small>{m.distance_km}km · +{m.reward_xp} XP</small></div>{m.completed&&<CheckCircle2 className="mission-check"/>}</article>)}</div></main>}
function HistoryPage({data}){return <main className="content-page"><PageTitle label="MY LOG" title="연습 히스토리" description="완주한 코스와 성장 기록을 확인해 보세요." Icon={BookOpen}/>{data.history?.length?<div className="history-list">{data.history.map(h=><article className="app-card" key={h.drive_id}><div className="history-icon"><CarFront size={17}/></div><div><h3>{h.course_name}</h3><p>안전하게 왕복 미션을 완료했어요.</p></div><div><b>+{h.xp_earned} XP</b><small>{h.distance_km}km · {h.actual_minutes}분</small></div></article>)}</div>:<div className="empty app-card"><BookOpen size={30}/><h3>아직 완료한 연습이 없어요</h3><p>추천 루트를 선택하고 첫 미션을 완주해 보세요.</p></div>}</main>}
function CommunityPage({data,onLike}){return <main className="content-page"><PageTitle label="TOGETHER" title="운전 커뮤니티" description="초보 운전자끼리 안전한 연습 팁을 나눠요." Icon={MessageCircle}/><div className="community-list">{data.posts.map(p=><article className="community app-card" key={p.post_id}><div className="avatar">🚗</div><div><div className="community-meta"><span className={cls('category',p.category)}>{p.category}</span><small>{p.nickname} · {p.created_at}</small></div><h3>{p.title}</h3><p>{p.content}</p><div className="community-actions"><button onClick={()=>onLike(p.post_id)}><Heart size={14}/>공감 {p.likes}</button><span><MessageCircle size={14}/>댓글 {p.comment_count}</span></div></div></article>)}</div></main>}

function PreviewModal({course,preview,loading,onClose,onStart}){return <div className="modal-layer" role="dialog" aria-modal="true" onMouseDown={e=>{if(e.target===e.currentTarget)onClose();}}><section className="preview-modal"><button className="modal-close" onClick={onClose}><X/></button><div className="preview-header"><span>ROUTE PREVIEW</span><h2>{course.course_name}</h2><p>{course.reason}</p></div><div className="preview-map">{loading?<div className="preview-loading"><Navigation/><b>실도로 경로를 불러오는 중…</b></div>:<RouteFallback coords={preview?.route_coords||course.route_coords}/>}</div><div className="preview-source"><ShieldCheck size={15}/><span>{preview?.message||'저장된 검증 경유지 기반 미리보기입니다.'}</span></div><div className="preview-grid"><div><b>{preview?.duration_minutes||course.estimated_minutes}분</b><small>예상 시간</small></div><div><b>{preview?.distance_km||course.distance_km}km</b><small>왕복 거리</small></div><div><b>{course.metrics?.right_turn_count||0}회</b><small>우회전</small></div></div><button className="primary" onClick={()=>onStart(course)}><Play size={16}/>이 코스로 연습 시작하기</button></section></div>}
function FinishModal({drive,onClose}){return <div className="modal-layer"><section className="finish-modal"><img src={CHARACTER}/><span>MISSION COMPLETE</span><h2>오늘의 미션 완료! 🎉</h2><p>안전하게 완주했어요.<br/><b>+{drive?.xp_earned||0} XP</b>를 획득했습니다.</p><button className="primary" onClick={onClose}>성장 기록 확인하기</button></section></div>}
function DriveBar({active,onCancel,onFinish}){return active?<div className="drive-bar"><div className="drive-bar-icon"><Navigation size={18}/></div><div><small>DRIVING NOW</small><b>{active.course_name}</b><span>안전한 곳에 정차한 뒤 종료해 주세요.</span></div><div className="drive-actions"><button onClick={onCancel}>취소</button><button onClick={onFinish}>주행 종료</button></div></div>:null}

function App(){
  const [data,setData]=useState({profile:{},zones:[],missions:[],history:[],posts:[]});
  const [tab,setTab]=useState('home'); const [courses,setCourses]=useState([]); const [coords,setCoords]=useState(DEFAULT_COORDS);
  const [filters,setFilters]=useState({zone_id:'',minutes:30,practice_type:'lane_keep',level:'beginner',avoid:['u_turn','accident_hotspot']});
  const [loading,setLoading]=useState(true); const [policy,setPolicy]=useState(''); const [preview,setPreview]=useState(null); const [previewData,setPreviewData]=useState(null); const [previewLoading,setPreviewLoading]=useState(false);
  const [active,setActive]=useState(null); const [navMode,setNavMode]=useState(false); const [finish,setFinish]=useState(null); const [toast,setToast]=useState('');
  const notify=(message)=>{setToast(message);setTimeout(()=>setToast(''),2100)};
  const refresh=async()=>{const boot=await api('/app/bootstrap/');setData(boot);setFilters(f=>({...f,zone_id:f.zone_id||String(boot.zones?.[0]?.zone_id||'')}));};
  useEffect(()=>{refresh().catch(e=>notify(e.message)).finally(()=>setLoading(false));},[]);
  const zone=useMemo(()=>data.zones.find(z=>String(z.zone_id)===String(filters.zone_id))||data.zones[0]||DEFAULT_ZONE,[data.zones,filters.zone_id]);
  async function recommend(){setLoading(true);try{const res=await api('/courses/recommend/',{method:'POST',body:JSON.stringify({...filters,zone_id:Number(filters.zone_id)})});setCourses(res.courses||[]);setPolicy(res.policy_message||'');if(res.courses?.[0]?.route_coords)setCoords(res.courses[0].route_coords);notify('오늘의 맞춤 코스를 찾았어요!');}catch(e){notify(e.message);}finally{setLoading(false)}}
  async function openPreview(course){setPreview(course);setPreviewData(null);setPreviewLoading(true);try{const res=await api(`/courses/${course.course_id}/preview/`);setPreviewData(res);setCoords(res.route_coords||course.route_coords||DEFAULT_COORDS);}catch(e){notify(e.message);setPreviewData({route_coords:course.route_coords,message:'실도로 경로를 불러오지 못해 검증 경유지로 표시합니다.'});}finally{setPreviewLoading(false)}}
  async function start(course){try{const res=await api('/drives/start/',{method:'POST',body:JSON.stringify({course_id:course.course_id})});let nav=previewData&&preview?.course_id===course.course_id?previewData:null;if(!nav){try{nav=await api(`/courses/${course.course_id}/preview/`);}catch(e){nav={route_coords:course.route_coords||DEFAULT_COORDS,navigation_instructions:[]};}}const route=nav?.route_coords||course.route_coords||DEFAULT_COORDS;setCoords(route);setActive({...res.drive,...course,route_coords:route,navigation_instructions:nav?.navigation_instructions||[],distance_km:nav?.distance_km||course.distance_km,duration_minutes:nav?.duration_minutes||course.estimated_minutes});setPreview(null);setNavMode(true);notify('내비게이션을 시작했어요. 안전운전하세요!');}catch(e){notify(e.message)}}
  async function cancel(){if(!active)return;try{await api(`/drives/${active.drive_id}/cancel/`,{method:'POST'});setActive(null);setNavMode(false);notify('주행을 취소했어요.');}catch(e){notify(e.message)}}
  async function complete(){if(!active)return;try{const res=await api(`/drives/${active.drive_id}/finish/`,{method:'POST',body:JSON.stringify({actual_minutes:active.actual_minutes||30})});setActive(null);setNavMode(false);setFinish(res.drive);await refresh();}catch(e){notify(e.message)}}
  async function like(postId){try{await api(`/community/posts/${postId}/like/`,{method:'POST'});await refresh();}catch(e){notify(e.message)}}
  if(loading&&!data.zones.length)return <div className="loading"><img src={CHARACTER}/><h1>오라이</h1><p>안전한 연습 코스를 준비하고 있어요.</p></div>;
  if(active&&navMode)return <><NavigationScreen active={active} zone={zone} onExit={cancel} onFinish={complete}/>{toast&&<div className="toast">{toast}</div>}</>;
  return <div className="app-shell"><SideNav tab={tab} setTab={setTab} profile={data.profile}/><section className="main-shell"><header className="mobile-header"><Brand/><div><b>Lv.{data.profile?.level||1}</b><img src={CHARACTER}/></div></header>{tab==='home'&&<MapStage coords={coords} zone={zone} active={active}/>} {tab==='home'?<HomePage data={data} filters={filters} setFilters={setFilters} courses={courses} onRecommend={recommend} onPreview={openPreview} onStart={start} loading={loading} policy={policy}/>:tab==='mission'?<MissionPage data={data}/>:tab==='history'?<HistoryPage data={data}/>:<CommunityPage data={data} onLike={like}/>}</section><BottomNav tab={tab} setTab={setTab}/><DriveBar active={active} onCancel={cancel} onFinish={complete}/>{preview&&<PreviewModal course={preview} preview={previewData} loading={previewLoading} onClose={()=>setPreview(null)} onStart={start}/>} {finish&&<FinishModal drive={finish} onClose={()=>{setFinish(null);setTab('mission')}}/>}{toast&&<div className="toast">{toast}</div>}</div>
}

createRoot(document.getElementById('root')).render(<App/>);
