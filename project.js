(() => {
  const form = document.getElementById('projectBriefForm');
  if (!form) return;
  const fields = {
    name: document.getElementById('clientName'),
    email: document.getElementById('clientEmail'),
    type: document.getElementById('projectType'),
    platform: document.getElementById('projectPlatform'),
    stage: document.getElementById('projectStage'),
    budget: document.getElementById('projectBudget'),
    message: document.getElementById('projectMessage'),
    consent: document.getElementById('projectConsent')
  };
  const status = document.getElementById('projectFormStatus');
  const copyBtn = document.getElementById('copyBriefBtn');

  const params = new URLSearchParams(location.search);
  const requestedType = params.get('type');
  if (requestedType && fields.type) {
    const match = [...fields.type.options].find(o => o.text.toLowerCase() === requestedType.toLowerCase());
    if (match) fields.type.value = match.value;
  }

  function currentLang(){ return document.documentElement.lang === 'en' ? 'en' : 'tr'; }
  function buildBrief(){
    const en = currentLang() === 'en';
    const v = el => (el?.value || '').trim();
    return [
      en ? 'VictoriumSoft Project Quote Request' : 'VictoriumSoft Proje Teklif Talebi',
      '----------------------------------------',
      `${en ? 'Name / Company' : 'Ad / Şirket'}: ${v(fields.name) || '-'}`,
      `E-mail: ${v(fields.email) || '-'}`,
      `${en ? 'Project type' : 'Proje türü'}: ${v(fields.type) || '-'}`,
      `${en ? 'Target platform' : 'Hedef platform'}: ${v(fields.platform) || '-'}`,
      `${en ? 'Current stage' : 'Proje durumu'}: ${v(fields.stage) || '-'}`,
      `${en ? 'Budget status' : 'Bütçe durumu'}: ${v(fields.budget) || '-'}`,
      '',
      en ? 'Project description:' : 'Proje açıklaması:',
      v(fields.message) || '-'
    ].join('\n');
  }

  form.addEventListener('submit', e => {
    e.preventDefault();
    const email = fields.email.value.trim();
    if (!email || !fields.type.value || !fields.message.value.trim() || !fields.consent.checked) {
      status.textContent = currentLang() === 'en' ? 'Please complete the required fields and accept the consent checkbox.' : 'Lütfen zorunlu alanları doldurun ve onay kutusunu işaretleyin.';
      status.classList.add('error');
      return;
    }
    status.textContent = '';
    status.classList.remove('error');
    const subject = currentLang() === 'en' ? `VictoriumSoft Quote Request - ${fields.type.value}` : `VictoriumSoft Teklif Talebi - ${fields.type.value}`;
    const mailto = `mailto:victoriumsoft@gmail.com?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(buildBrief())}`;
    window.location.href = mailto;
  });

  copyBtn?.addEventListener('click', async () => {
    try {
      await navigator.clipboard.writeText(buildBrief());
      status.textContent = currentLang() === 'en' ? 'Project summary copied.' : 'Proje özeti kopyalandı.';
      status.classList.remove('error');
    } catch {
      status.textContent = currentLang() === 'en' ? 'Could not copy automatically.' : 'Otomatik kopyalama yapılamadı.';
      status.classList.add('error');
    }
  });
})();