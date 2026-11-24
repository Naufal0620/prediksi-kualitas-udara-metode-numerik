(() => {
  'use strict';
  const THRESHOLD = 55;
  const state = { days: 1, city: 'medan', stations: [], map: null, chart: null, markers: {}, hotspots: null };
  const $ = id => document.getElementById(id);
  const fmt = (v, n = 2) => Number.isFinite(Number(v)) ? Number(v).toFixed(n) : '—';
  const escapeHtml = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));

  function status(online, label) {
    $('apiStatus').classList.toggle('online', online);
    $('apiStatus').classList.toggle('offline', !online);
    $('apiStatusText').textContent = label;
  }
  function errorMessage(message) {
    $('globalError').textContent = message;
    $('globalError').classList.remove('d-none');
  }
  function clearError() { $('globalError').classList.add('d-none'); }
  function loading(value) { $('loadingOverlay').classList.toggle('d-none', !value); }

  async function apiGet(path) {
    let response;
    try { response = await fetch(path, { headers: { Accept: 'application/json' }, cache: 'no-store' }); }
    catch (e) { throw new Error(`Tidak dapat menghubungi API. Pastikan Flask aktif. Detail: ${e.message}`); }
    const raw = await response.text();
    let payload;
    try { payload = JSON.parse(raw); }
    catch (_) {
      if (response.status >= 500) throw new Error(`Server mengembalikan HTTP ${response.status}, bukan JSON. Periksa traceback di terminal Flask untuk penyebab Back-End.`);
      throw new Error(`Respons API bukan JSON (HTTP ${response.status}).`);
    }
    if (!response.ok) throw new Error(payload.error || `Permintaan gagal (HTTP ${response.status}).`);
    return payload;
  }

  function quality(value) {
    const n = Number(value);
    if (!Number.isFinite(n)) return {label:'Belum tersedia', color:'#91a1b7'};
    if (n <= 15.5) return {label:'Baik / Baik Sekali', color:'#10b981'};
    if (n <= THRESHOLD) return {label:'Sedang / Moderat', color:'#f59e0b'};
    return {label:'Tidak Sehat · Ambang terlampaui', color:'#ef4444'};
  }

  function initMap() {
    state.map = L.map('map', { scrollWheelZoom: true }).setView([-2.5, 118], 5);
    // OpenStreetMap tiles avoid requiring a CARTO API key.
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 19, subdomains: 'abc',
      attribution: '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a>'
    }).addTo(state.map);
    state.hotspots = L.layerGroup().addTo(state.map);
  }

  function initChart() {
    state.chart = new Chart($('predictionChart').getContext('2d'), {
      type: 'line',
      data: { datasets: [
        {label:'Prediksi diskrit',data:[],parsing:false,borderColor:'#2dd4bf',backgroundColor:'rgba(45,212,191,.10)',borderWidth:2,pointRadius:2.5,tension:.12},
        {label:'Kurva polinomial MA24',data:[],parsing:false,borderColor:'#38bdf8',backgroundColor:'transparent',borderWidth:2.4,pointRadius:0,tension:.25},
        {label:'Baku mutu 55 µg/m³',data:[],parsing:false,borderColor:'#ef4444',borderDash:[7,6],borderWidth:1.8,pointRadius:0}
      ]},
      options: {
        responsive:true, maintainAspectRatio:false, interaction:{mode:'index',intersect:false},
        plugins:{legend:{display:false},tooltip:{backgroundColor:'#0b1728',borderColor:'rgba(148,163,184,.2)',borderWidth:1,titleColor:'#e8f0fa',bodyColor:'#cbd5e1',callbacks:{label:c=>`${c.dataset.label}: ${fmt(c.parsed.y)} µg/m³`}}},
        scales:{
          x:{type:'linear',title:{display:true,text:'Jam ke depan',color:'#91a1b7'},grid:{color:'rgba(148,163,184,.08)'},ticks:{color:'#91a1b7',maxTicksLimit:12}},
          y:{beginAtZero:true,title:{display:true,text:'PM2.5 (µg/m³)',color:'#91a1b7'},grid:{color:'rgba(148,163,184,.08)'},ticks:{color:'#91a1b7'}}
        }
      }
    });
  }

  function renderStations(stations) {
    if (!Array.isArray(stations) || !stations.length) throw new Error('API /api/stations tidak mengirim daftar stasiun yang valid.');
    state.stations = stations;
    const select = $('stationSelect');
    select.replaceChildren();
    stations.forEach(station => {
      const option = document.createElement('option');
      option.value = station.key;
      option.textContent = station.name;
      select.appendChild(option);
      const lat = Number(station.coordinates?.latitude), lon = Number(station.coordinates?.longitude);
      if (Number.isFinite(lat) && Number.isFinite(lon)) {
        const marker = L.circleMarker([lat, lon], {radius:8,color:'#d7fffa',weight:1.5,fillColor:'#0d9488',fillOpacity:.95}).addTo(state.map);
        marker.bindPopup(`<strong>${escapeHtml(station.name)}</strong><br>${escapeHtml(station.city)}, ${escapeHtml(station.province)}<br>Akurasi: ${fmt(station.metrics?.accuracy_percent)}%`);
        marker.on('click', () => selectStation(station.key));
        state.markers[station.key] = marker;
      }
    });
    state.city = stations.some(s => s.key === state.city) ? state.city : stations[0].key;
    select.value = state.city;
    $('mapNotice').textContent = `${stations.length} stasiun tersedia`;
  }

  function renderMetrics(station) {
    if (!station) return;
    const m = station.metrics || {};
    $('metricStation').textContent = station.name || '—';
    $('metricProvince').textContent = station.province || station.city || '—';
    $('detailStationName').textContent = station.name || '—';
    $('detailStationLocation').textContent = `${station.city || '—'}, ${station.province || '—'}`;
    $('detailRegion').textContent = station.region_group || '—';
    $('metricAccuracy').textContent = fmt(m.accuracy_percent);
    $('statAccuracy').textContent = `${fmt(m.accuracy_percent)}%`;
    $('statMae').textContent = `${fmt(m.mae)} µg/m³`;
    $('statRmse').textContent = `${fmt(m.rmse)} µg/m³`;
    $('statMape').textContent = `${fmt(m.mape_percent)}%`;
  }

  function renderSecant(secant = {}, degree) {
    const safe = secant.status === 'SAFE';
    const danger = ['THRESHOLD_EXCEEDED','HAZARDOUS'].includes(secant.status);
    const card = $('secantCard');
    card.className = `warning-card ${safe ? 'warning-safe' : danger ? 'warning-danger' : 'warning-pending'}`;
    $('secantIcon').innerHTML = safe ? '<i class="bi bi-shield-check"></i>' : danger ? '<i class="bi bi-exclamation-triangle-fill"></i>' : '<i class="bi bi-info-circle"></i>';
    $('secantStatus').textContent = safe ? 'KUALITAS UDARA DIPREDIKSI AMAN' : danger ? 'PERINGATAN: AMBANG BATAS TERLAMPAUI' : 'STATUS ANALISIS TIDAK TERSEDIA';
    $('secantDesc').textContent = secant.message || 'Server tidak mengirimkan pesan analisis.';
    $('statIter').textContent = secant.iterations ?? '—';
    $('statResidual').textContent = secant.residual == null ? '—' : fmt(secant.residual, 6);
    $('statDegree').textContent = degree == null ? '—' : `Orde ${degree}`;
  }

  function renderPrediction(data) {
    const predictions = data.raw_predictions || [];
    const threshold = Number(data.air_quality_threshold ?? THRESHOLD);
    const hours = Number(data.forecast_horizon?.hours || predictions.length);
    const curve = data.polynomial_curve || {};
    const discrete = predictions.map((y,i)=>({x:i+1,y:Number(y)})).filter(p=>Number.isFinite(p.y));
    const smooth = (curve.points_x || []).map((x,i)=>({x:Number(x),y:Number(curve.points_y?.[i])})).filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));
    const ma24 = (data.ma24_discrete || []).map((y,i)=>({x:i+1,y:Number(y)})).filter(p=>Number.isFinite(p.y));
    state.chart.data.datasets[0].data = discrete;
    state.chart.data.datasets[1].data = smooth.length ? smooth : ma24;
    state.chart.data.datasets[2].data = [{x:1,y:threshold},{x:Math.max(hours,1),y:threshold}];
    state.chart.options.scales.x.max = Math.max(hours,1);
    state.chart.update();

    const latest = predictions.length ? Number(predictions[0]) : NaN;
    $('metricPm25').textContent = fmt(latest);
    const q = quality(latest);
    $('metricQuality').textContent = q.label;
    $('metricQuality').style.color = q.color;
    $('metricHorizon').textContent = hours <= 24 ? '24 Jam' : `${data.forecast_horizon?.days ?? hours/24} Hari`;
    $('metricForecastRange').textContent = `${data.forecast_horizon?.start_time || '—'} s/d ${data.forecast_horizon?.end_time || '—'}`;
    $('chartCaption').textContent = `${predictions.length} titik prediksi · Kurva polinomial derajat ${curve.degree ?? '—'} · Ambang batas ${threshold} µg/m³.`;
    $('lastUpdated').textContent = `Diperbarui ${new Date().toLocaleTimeString('id-ID',{hour:'2-digit',minute:'2-digit'})}`;
    renderSecant(data.secant_analysis || {}, curve.degree);
    const coords = data.station?.coordinates;
    if (coords && Number.isFinite(Number(coords.latitude)) && Number.isFinite(Number(coords.longitude))) {
      state.map.setView([Number(coords.latitude),Number(coords.longitude)],8,{animate:true});
    }
  }

  async function loadHotspots(city) {
    state.hotspots.clearLayers();
    try {
      const data = await apiGet(`/api/hotspots/${encodeURIComponent(city)}`);
      const points = data.hotspots || [];
      $('hotspotTotal').textContent = data.total ?? points.length;
      $('hotspotDescription').textContent = points.length
        ? `Terdapat ${points.length} titik api pada data tersedia untuk ${data.station_name || city}. Marker oranye ditampilkan pada peta.`
        : 'Tidak ada titik api yang tersedia pada data server untuk stasiun ini.';
      points.forEach(point => {
        const lat=Number(point.latitude), lon=Number(point.longitude);
        if (!Number.isFinite(lat)||!Number.isFinite(lon)) return;
        L.circleMarker([lat,lon],{radius:5,color:'#fed7aa',weight:1,fillColor:'#f97316',fillOpacity:.9})
          .bindPopup(`<strong>Hotspot</strong><br>Brightness: ${escapeHtml(point.brightness)}<br>Confidence: ${escapeHtml(point.confidence)}<br>Waktu: ${escapeHtml(point.timestamp)}`)
          .addTo(state.hotspots);
      });
      $('mapNotice').textContent = `${state.stations.length} stasiun · ${points.length} hotspot`;
    } catch (e) {
      $('hotspotTotal').textContent = '—';
      $('hotspotDescription').textContent = `Data hotspot tidak dapat dimuat: ${e.message}`;
    }
  }

  async function loadStation(city) {
    state.city = city;
    clearError();
    loading(true);
    renderMetrics(state.stations.find(s=>s.key===city));
    try {
      const prediction = await apiGet(`/api/predict/${encodeURIComponent(city)}?days=${state.days}`);
      renderPrediction(prediction);
      await loadHotspots(city);
      status(true,'REST API terhubung');
    } catch (e) {
      errorMessage(`Gagal memuat prediksi ${city}: ${e.message}`);
      status(false,'API bermasalah');
      renderSecant({message:e.message});
    } finally { loading(false); }
  }

  function selectStation(city) {
    $('stationSelect').value = city;
    loadStation(city);
  }

  async function boot() {
    $('currentDate').textContent = new Date().toLocaleDateString('id-ID',{weekday:'short',day:'numeric',month:'short',year:'numeric'});
    initMap();
    initChart();
    $('stationSelect').addEventListener('change',e=>selectStation(e.target.value));
    document.querySelectorAll('.horizon-btn').forEach(btn=>btn.addEventListener('click',()=>{
      state.days=Number(btn.dataset.days);
      document.querySelectorAll('.horizon-btn').forEach(b=>{
        const active=b===btn; b.classList.toggle('active',active); b.setAttribute('aria-pressed',String(active));
      });
      loadStation(state.city);
    }));
    $('refreshButton').addEventListener('click',()=>loadStation(state.city));
    $('menuToggle').addEventListener('click',()=> $('sidebar').classList.toggle('open'));
    document.querySelectorAll('.side-link').forEach(link=>link.addEventListener('click',()=>{
      document.querySelectorAll('.side-link').forEach(x=>x.classList.toggle('active',x===link));
      $('sidebar').classList.remove('open');
    }));

    try {
      const health=await apiGet('/api/health');
      status(health.status==='online',health.status==='online'?'REST API terhubung':'API tidak aktif');
      const stations=await apiGet('/api/stations');
      renderStations(stations.stations || []);
      await loadStation(state.city);
    } catch(e) {
      status(false,'API tidak terhubung');
      errorMessage(`Tidak dapat mengambil data dari API. Buka dashboard melalui Flask (http://127.0.0.1:5000), bukan double-click file HTML. Detail: ${e.message}`);
      $('mapNotice').textContent='Data stasiun belum tersedia';
      loading(false);
    }
  }
  document.addEventListener('DOMContentLoaded',boot);
})();
