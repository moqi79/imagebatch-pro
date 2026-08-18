// ImageBatch Pro Web UI
let appStatus = null;
let selectedFiles = [];

// ---- 初始化 ----
async function init() {
    await loadStatus();
    await loadPresets();
}

async function api(url, method = 'GET', body = null) {
    const opts = { method, headers: { 'Content-Type': 'application/json' } };
    if (body) opts.body = JSON.stringify(body);
    const resp = await fetch(url, opts);
    return resp.json();
}

// ---- 状态 ----
async function loadStatus() {
    const data = await api('/api/status');
    appStatus = data;
    document.getElementById('version').textContent = 'v' + data.version;

    const badge = document.getElementById('licenseBadge');
    if (data.edition === 'pro') {
        badge.textContent = '专业版';
        badge.className = 'badge badge-pro';
        document.getElementById('btnUpgrade').style.display = 'none';
    } else if (data.edition === 'studio') {
        badge.textContent = '工作室版';
        badge.className = 'badge badge-studio';
        document.getElementById('btnUpgrade').style.display = 'none';
    } else {
        badge.textContent = '社区版';
        badge.className = 'badge badge-free';
    }

    document.getElementById('licenseInfo').textContent = data.summary;

    const featDiv = document.getElementById('licenseFeatures');
    featDiv.innerHTML = data.features.map(f =>
        `<span class="feature-tag">${f.name}</span>`
    ).join('');

    // 专业版功能解锁
    const hasPro = data.edition === 'pro' || data.edition === 'studio';
    toggleLock('watermarkCard', 'wmLock', hasPro);
    toggleLock('exifCard', 'exifLock', hasPro);
}

function toggleLock(cardId, lockId, unlocked) {
    const card = document.getElementById(cardId);
    const lock = document.getElementById(lockId);
    if (unlocked) {
        card.classList.remove('card-locked');
        lock.style.display = 'none';
    } else {
        card.classList.add('card-locked');
        lock.style.display = 'inline';
    }
}

// ---- 预设 ----
async function loadPresets() {
    const data = await api('/api/presets');
    const sel = document.getElementById('presetSelect');
    if (sel.children.length > 1) return;
    for (const [id, p] of Object.entries(data.presets)) {
        const opt = document.createElement('option');
        opt.value = id;
        opt.textContent = p.name + ' — ' + (p.description || '');
        sel.appendChild(opt);
    }
    sel.onchange = () => {
        const desc = document.getElementById('presetDesc');
        const preset = data.presets[sel.value];
        if (preset) {
            desc.textContent = preset.description || '';
            desc.style.display = 'block';
        } else {
            desc.style.display = 'none';
        }
    };
}

// ---- 目录扫描 ----
async function scanDir() {
    const dir = document.getElementById('inputDir').value.trim();
    if (!dir) { alert('请输入图片目录路径'); return; }

    const data = await api('/api/select-dir', 'POST', { path: dir });
    const list = document.getElementById('fileList');

    if (data.error) {
        list.innerHTML = `<div class="file-list-empty" style="color:var(--danger)">${data.error}</div>`;
        return;
    }

    selectedFiles = data.files;
    if (data.count === 0) {
        list.innerHTML = '<div class="file-list-empty">未找到图片文件（支持 JPG/PNG/WebP/BMP/TIFF/GIF）</div>';
        return;
    }

    list.innerHTML = `<div style="font-size:12px;color:var(--text-light);padding:4px 8px">
        找到 ${data.count} 张图片</div>`;
    data.files.slice(0, 50).forEach(f => {
        const sizeKB = (f.size / 1024).toFixed(0);
        list.innerHTML += `<div class="file-list-item">
            <span>${f.name}</span><span>${sizeKB} KB</span></div>`;
    });
    if (data.count > 50) {
        list.innerHTML += `<div class="file-list-empty">... 还有 ${data.count - 50} 张</div>`;
    }

    document.getElementById('footerStatus').textContent = `已扫描 ${data.count} 张图片`;
}

// ---- 处理 ----
async function startProcessing() {
    const inputDir = document.getElementById('inputDir').value.trim();
    if (!inputDir) { alert('请先选择图片目录并扫描'); return; }

    const outputDir = document.getElementById('outputDir').value.trim();

    const body = {
        input_dir: inputDir,
        output_dir: outputDir,
    };

    if (document.getElementById('enableCompress').checked) {
        body.compress = parseInt(document.getElementById('compressTarget').value);
    }

    if (document.getElementById('enableResize').checked) {
        body.resize = {
            width: parseInt(document.getElementById('resizeW').value),
            height: parseInt(document.getElementById('resizeH').value),
            mode: document.getElementById('resizeMode').value,
        };
    }

    if (document.getElementById('enableFormat').checked) {
        body.format = document.getElementById('formatSelect').value;
    }

    if (document.getElementById('enableWatermark').checked) {
        body.watermark = {
            text: document.getElementById('wmText').value,
            position: document.getElementById('wmPosition').value,
            size: parseInt(document.getElementById('wmSize').value),
            color: document.getElementById('wmColor').value,
            opacity: parseInt(document.getElementById('wmOpacity').value) / 100,
        };
    }

    if (document.getElementById('enableClearExif').checked) {
        body.clear_exif = true;
    }

    const preset = document.getElementById('presetSelect').value;
    if (preset) body.preset = preset;

    // UI 状态
    const btn = document.getElementById('btnStart');
    btn.disabled = true;
    btn.textContent = '⏳ 处理中...';
    document.getElementById('progressArea').style.display = 'block';
    document.getElementById('progressBar').style.width = '50%';
    document.getElementById('progressText').textContent = '正在处理图片...';
    document.getElementById('footerStatus').textContent = '处理中...';

    try {
        const data = await api('/api/process', 'POST', body);

        document.getElementById('progressBar').style.width = '100%';
        document.getElementById('progressText').textContent = '处理完成！';

        if (data.error) {
            alert('处理失败: ' + data.error);
        } else {
            showResults(data);
        }
    } catch (e) {
        alert('请求失败: ' + e.message);
    } finally {
        btn.disabled = false;
        btn.textContent = '▶ 开始处理';
        setTimeout(() => {
            document.getElementById('progressArea').style.display = 'none';
        }, 2000);
        document.getElementById('footerStatus').textContent = '就绪';
    }
}

function showResults(data) {
    const area = document.getElementById('resultArea');
    area.style.display = 'block';

    const inKB = (data.input_size / 1024).toFixed(0);
    const outKB = (data.output_size / 1024).toFixed(0);

    document.getElementById('resultSummary').innerHTML = `
        <div class="result-stat"><div class="num">${data.success}</div><div class="label">成功</div></div>
        <div class="result-stat"><div class="num">${data.failed}</div><div class="label">失败</div></div>
        <div class="result-stat"><div class="num">${inKB}KB</div><div class="label">原始体积</div></div>
        <div class="result-stat"><div class="num">${outKB}KB</div><div class="label">输出体积</div></div>
    `;

    const list = document.getElementById('resultList');
    list.innerHTML = data.results.map(r => {
        const inS = (r.input_size / 1024).toFixed(0);
        const outS = (r.output_size / 1024).toFixed(0);
        const status = r.success
            ? '<span class="status-ok">✓</span>'
            : `<span class="status-fail">✗ ${r.error}</span>`;
        return `<div class="result-item">
            <span>${r.name}</span>
            <span>${inS}KB → ${r.success ? outS + 'KB' : '-'} ${status}</span>
        </div>`;
    }).join('');
}

// ---- 升级弹窗 ----
function openModal(id) {
    document.getElementById(id).style.display = 'flex';
}
function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

document.getElementById('btnUpgrade').onclick = () => openModal('upgradeModal');
document.getElementById('btnAbout').onclick = () => openModal('aboutModal');

let selectedEdition = null;
function selectEdition(edition) {
    selectedEdition = edition;
    document.querySelectorAll('.pricing-card').forEach(c => c.style.borderColor = '');
    event.currentTarget.style.borderColor = 'var(--primary)';
    generateOrder(edition);
}

async function generateOrder(edition) {
    const data = await api('/api/pay', 'POST', { edition });
    if (data.order) {
        document.getElementById('orderSection').style.display = 'block';
        document.getElementById('orderText').textContent =
            data.text + '\n支付确认码: ' + data.order.confirm_code;
        document.getElementById('confirmCode').value = data.order.confirm_code;
    }
}

async function confirmPayment() {
    const code = document.getElementById('confirmCode').value.trim();
    if (!code) { alert('请输入支付确认码'); return; }

    const data = await api('/api/confirm-payment', 'POST', { code });
    if (data.success) {
        alert(data.message);
        closeModal('upgradeModal');
        await loadStatus();
    } else {
        alert('激活失败: ' + data.message);
    }
}

// ---- 启动 ----
init();
