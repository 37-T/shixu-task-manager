const labels = { todo: '待办', in_progress: '进行中', done: '已完成' };
const priorityLabels = { low: '较低', medium: '普通', high: '较高' };
const state = { filter: 'all', query: '', tasks: [] };
const $ = (selector) => document.querySelector(selector);
const list = $('#task-list');
const dialog = $('#task-dialog');
let toastTimer;

async function request(url, options = {}) {
  const response = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...options });
  if (!response.ok) {
    let message = '操作失败，请稍后重试。';
    try { const data = await response.json(); message = typeof data.detail === 'string' ? data.detail : '请检查填写内容是否正确。'; } catch {}
    throw new Error(message);
  }
  return response.status === 204 ? null : response.json();
}

async function refresh() {
  list.innerHTML = '<div class="loading">正在整理任务…</div>';
  const params = new URLSearchParams();
  if (state.filter !== 'all') params.set('status', state.filter);
  if (state.query.trim()) params.set('q', state.query.trim());
  try {
    const [tasks, summary] = await Promise.all([request(`/api/tasks?${params}`), request('/api/summary')]);
    state.tasks = tasks;
    $('#count-total').textContent = summary.total;
    $('#count-todo').textContent = summary.todo;
    $('#count-in-progress').textContent = summary.in_progress;
    $('#count-done').textContent = summary.done;
    $('#visible-count').textContent = `${tasks.length} 项`;
    renderTasks(tasks);
  } catch (error) {
    list.innerHTML = `<div class="empty error-state"><span>!</span><p>${escapeHtml(error.message)}<br>请确认服务已正常启动。</p></div>`;
  }
}

function escapeHtml(value = '') {
  return String(value).replace(/[&<>"']/g, (char) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[char]));
}

function formatDate(value) {
  if (!value) return '';
  const [year, month, day] = value.split('-');
  return `${year}/${month}/${day}`;
}

function renderTasks(tasks) {
  if (!tasks.length) {
    list.innerHTML = `<div class="empty"><span>✳</span><p>${state.query || state.filter !== 'all' ? '没有找到符合条件的任务' : '这里还空着，添加一件要做的事吧'}</p></div>`;
    return;
  }
  list.innerHTML = tasks.map((task) => `
    <article class="task-row">
      <div class="task-main">
        <div class="task-title-line"><span class="task-title ${task.status === 'done' ? 'is-done' : ''}">${escapeHtml(task.title)}</span><span class="badge ${task.status}">${labels[task.status]}</span></div>
        <div class="task-meta"><span class="priority ${task.priority}"><i class="priority-dot"></i>${priorityLabels[task.priority]}优先级</span>${task.due_date ? `<span>◷ ${formatDate(task.due_date)} 截止</span>` : ''}</div>
        ${task.description ? `<p class="task-description">${escapeHtml(task.description)}</p>` : ''}
      </div>
      <div class="row-actions"><button data-action="toggle" data-id="${task.id}">${task.status === 'done' ? '恢复待办' : '标记完成'}</button><button data-action="edit" data-id="${task.id}">编辑</button><button data-action="delete" data-id="${task.id}">删除</button></div>
    </article>`).join('');
}

function showToast(message) {
  const toast = $('#toast'); toast.textContent = message; toast.classList.add('show');
  clearTimeout(toastTimer); toastTimer = setTimeout(() => toast.classList.remove('show'), 2200);
}

function openForm(task = null) {
  $('#task-form').reset(); $('#form-error').textContent = '';
  $('#dialog-title').textContent = task ? '编辑任务' : '新建任务';
  $('#task-id').value = task?.id || '';
  if (task) {
    $('#title').value = task.title; $('#description').value = task.description;
    $('#due-date').value = task.due_date || ''; $('#priority').value = task.priority; $('#status').value = task.status;
  } else {
    $('#priority').value = 'medium'; $('#status').value = 'todo';
  }
  dialog.showModal(); $('#title').focus();
}

$('#new-task').addEventListener('click', () => openForm());
$('#close-dialog').addEventListener('click', () => dialog.close());
$('#cancel-dialog').addEventListener('click', () => dialog.close());
$('#search').addEventListener('input', (event) => { state.query = event.target.value; refresh(); });
document.querySelectorAll('.filter').forEach((button) => button.addEventListener('click', () => {
  document.querySelector('.filter.active').classList.remove('active'); button.classList.add('active'); state.filter = button.dataset.filter; refresh();
}));

$('#task-form').addEventListener('submit', async (event) => {
  event.preventDefault();
  const id = $('#task-id').value;
  const payload = { title: $('#title').value.trim(), description: $('#description').value.trim(), due_date: $('#due-date').value || null, priority: $('#priority').value, status: $('#status').value };
  try {
    await request(id ? `/api/tasks/${id}` : '/api/tasks', { method: id ? 'PATCH' : 'POST', body: JSON.stringify(payload) });
    dialog.close(); showToast(id ? '任务已更新' : '任务已添加'); await refresh();
  } catch (error) { $('#form-error').textContent = error.message; }
});

list.addEventListener('click', async (event) => {
  const button = event.target.closest('button[data-action]'); if (!button) return;
  const task = state.tasks.find((item) => item.id === Number(button.dataset.id)); if (!task) return;
  try {
    if (button.dataset.action === 'edit') { openForm(task); return; }
    if (button.dataset.action === 'delete') {
      if (!window.confirm(`确定删除“${task.title}”吗？`)) return;
      await request(`/api/tasks/${task.id}`, { method: 'DELETE' }); showToast('任务已删除');
    } else {
      await request(`/api/tasks/${task.id}`, { method: 'PATCH', body: JSON.stringify({ status: task.status === 'done' ? 'todo' : 'done' }) });
      showToast(task.status === 'done' ? '任务已恢复' : '做得好，任务完成了');
    }
    await refresh();
  } catch (error) { showToast(error.message); }
});

refresh();
