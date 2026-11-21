"use strict";
(()=>{
  const menu=document.getElementById('menuBtn'); const mobile=document.getElementById('mobileMenu');
  const close=()=>{if(!menu||!mobile)return;mobile.classList.remove('open');menu.classList.remove('active');menu.setAttribute('aria-expanded','false')};
  if(menu&&mobile){menu.addEventListener('click',()=>{let isOpen=mobile.classList.toggle('open');menu.classList.toggle('active',isOpen);menu.setAttribute('aria-expanded',String(isOpen));});mobile.querySelectorAll('a').forEach(x=>x.addEventListener('click',close));document.addEventListener('keydown',e=>{if(e.key==='Escape')close()});}
  const filters=document.querySelectorAll('.filter[data-filter]');const cards=document.querySelectorAll('.app-card[data-kind]');
  filters.forEach(btn=>btn.addEventListener('click',()=>{filters.forEach(x=>x.classList.remove('active'));btn.classList.add('active');const type=btn.dataset.filter;cards.forEach(card=>{card.hidden=type!=='all'&&card.dataset.kind!==type;})}));
  function launchEmail(to,subject,body){location.href='mailto:'+to+'?subject='+encodeURIComponent(subject)+'&body='+encodeURIComponent(body)}
  const tester=document.getElementById('testerForm');if(tester)tester.addEventListener('submit',e=>{e.preventDefault();if(!tester.reportValidity())return;const email=document.getElementById('testerEmail').value.trim();const project=document.getElementById('testerProject').value;launchEmail('victoriumsoft@gmail.com','Tester Başvurusu - '+project,'Proje: '+project+'\nE-posta: '+email+'\nKapalı test başvurusu yapmak istiyorum.')});
  const project=document.getElementById('projectForm');if(project)project.addEventListener('submit',e=>{e.preventDefault();if(!project.reportValidity())return;const name=document.getElementById('projectName').value.trim();const email=document.getElementById('projectEmail').value.trim();const type=document.getElementById('projectType').value;const desc=document.getElementById('projectDesc').value.trim();launchEmail('victoriumsoft@gmail.com','Proje Teklifi - '+type,'İsim: '+name+'\nE-posta: '+email+'\nTür: '+type+'\n\nProje:\n'+desc)});
  if(location.protocol==='https:'&&'serviceWorker' in navigator){window.addEventListener('load',()=>navigator.serviceWorker.register('service-worker.js').catch(()=>{}));}
})();
