let calendarInstance = null;
let calendars = [];
let events = [];
let activeCalendarIds = new Set();
let currentEventId = null;
let currentEventPerm = 'read';
let allUsers = [];

document.addEventListener('DOMContentLoaded', async () => {
    // Inicializar FullCalendar
    const calendarEl = document.getElementById('calendar');
    calendarInstance = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        locale: 'pt-br',
        editable: true,
        selectable: true,
        select: handleDateSelect,
        eventClick: handleEventClick,
        eventDrop: handleEventDrop,
        eventResize: handleEventDrop,
        events: fetchEvents
    });
    calendarInstance.render();

    await loadCalendars();
    await loadUsers();
});

// Mock da API para simplificar. Substituir por chamadas reais via axios/fetch usando o token JWT
async function apiGet(endpoint) {
    const token = localStorage.getItem('ordersync_token');
    const baseUrl = window.API_BASE || '';
    const res = await fetch(`${baseUrl}/api/v1${endpoint}`, {
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
}

async function apiPost(endpoint, data) {
    const token = localStorage.getItem('ordersync_token');
    const baseUrl = window.API_BASE || '';
    const res = await fetch(`${baseUrl}/api/v1${endpoint}`, {
        method: 'POST',
        headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
}

async function apiPut(endpoint, data) {
    const token = localStorage.getItem('ordersync_token');
    const baseUrl = window.API_BASE || '';
    const res = await fetch(`${baseUrl}/api/v1${endpoint}`, {
        method: 'PUT',
        headers: { 
            'Authorization': `Bearer ${token}`,
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(data)
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
}

async function apiDelete(endpoint) {
    const token = localStorage.getItem('ordersync_token');
    const baseUrl = window.API_BASE || '';
    const res = await fetch(`${baseUrl}/api/v1${endpoint}`, {
        method: 'DELETE',
        headers: { 'Authorization': `Bearer ${token}` }
    });
    if (!res.ok) throw new Error('API Error');
    return res.json();
}

async function loadCalendars() {
    try {
        calendars = await apiGet('/calendars');
        activeCalendarIds = new Set(calendars.map(c => c.id));
        renderCalendarSidebar();
        calendarInstance.refetchEvents();
    } catch (e) {
        console.error("Erro ao carregar calendários", e);
    }
}

async function loadUsers() {
    try {
        const token = localStorage.getItem('ordersync_token');
        const baseUrl = window.API_BASE || '';
        const res = await fetch(`${baseUrl}/usuarios/lookup`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!res.ok) throw new Error('API Error');
        allUsers = await res.json();
        renderUsersList();
    } catch (e) {
        console.error("Erro ao carregar usuários", e);
    }
}

function renderUsersList() {
    const listEl = document.getElementById('event-share-users-list');
    if (!listEl) return;
    listEl.innerHTML = '';
    
    // Pegar o próprio email para não exibir
    const token = localStorage.getItem('ordersync_token');
    let myEmail = '';
    if(token) {
        try {
            const payload = JSON.parse(atob(token.split('.')[1]));
            myEmail = payload.sub || '';
        } catch(e) {}
    }

    allUsers.forEach(u => {
        if (u.email === myEmail) return;
        
        const div = document.createElement('div');
        div.style.marginBottom = '5px';
        div.style.display = 'flex';
        div.style.alignItems = 'center';
        
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.value = u.email;
        cb.id = `share-user-${u.id}`;
        cb.className = 'share-user-checkbox';
        cb.style.marginRight = '8px';
        
        const lbl = document.createElement('label');
        lbl.htmlFor = cb.id;
        lbl.textContent = `${u.nome || u.email} (${u.email})`;
        lbl.style.fontSize = '0.85rem';
        lbl.style.cursor = 'pointer';
        
        const permSelect = document.createElement('select');
        permSelect.className = 'share-user-perm';
        permSelect.id = `share-perm-${u.id}`;
        permSelect.style.marginLeft = 'auto';
        permSelect.style.padding = '2px 4px';
        permSelect.style.fontSize = '0.75rem';
        permSelect.innerHTML = '<option value="read">Leitura</option><option value="write">Escrita</option>';
        permSelect.disabled = true;

        cb.onchange = () => {
            permSelect.disabled = !cb.checked;
        };
        
        div.appendChild(cb);
        div.appendChild(lbl);
        div.appendChild(permSelect);
        listEl.appendChild(div);
    });
}

function renderCalendarSidebar() {
    const ownList = document.getElementById('own-calendars-list');
    const sharedList = document.getElementById('shared-calendars-list');
    
    ownList.innerHTML = '';
    sharedList.innerHTML = '';
    
    const selectCal = document.getElementById('event-calendar');
    selectCal.innerHTML = '';

    calendars.forEach(cal => {
        const isOwner = cal.permission_level === 'admin';
        
        // Checkbox element
        const div = document.createElement('div');
        div.className = 'calendar-item';
        
        const cb = document.createElement('input');
        cb.type = 'checkbox';
        cb.checked = activeCalendarIds.has(cal.id);
        cb.onchange = (e) => {
            if (e.target.checked) activeCalendarIds.add(cal.id);
            else activeCalendarIds.delete(cal.id);
            calendarInstance.refetchEvents();
        };
        
        const dot = document.createElement('div');
        dot.className = 'color-dot';
        dot.style.backgroundColor = cal.color;
        
        const span = document.createElement('span');
        span.className = 'calendar-name';
        span.textContent = cal.name;
        
        div.appendChild(cb);
        div.appendChild(dot);
        div.appendChild(span);
        
        if (isOwner) {
            const shareBtn = document.createElement('button');
            shareBtn.innerHTML = '&#128101;'; // Ícone de pessoas
            shareBtn.style.marginLeft = 'auto';
            shareBtn.style.border = 'none';
            shareBtn.style.background = 'none';
            shareBtn.style.cursor = 'pointer';
            shareBtn.style.fontSize = '12px';
            shareBtn.title = 'Compartilhar Agenda';
            shareBtn.onclick = () => openShareModal(cal.id);
            
            div.appendChild(shareBtn);
            ownList.appendChild(div);
        } else {
            const badge = document.createElement('span');
            badge.className = 'calendar-badge';
            badge.textContent = cal.permission_level;
            div.appendChild(badge);
            sharedList.appendChild(div);
        }
        
        // Option for select
        if (cal.permission_level === 'write' || cal.permission_level === 'admin') {
            const opt = document.createElement('option');
            opt.value = cal.id;
            opt.textContent = cal.name;
            selectCal.appendChild(opt);
        }
    });
}

async function fetchEvents(info, successCallback, failureCallback) {
    try {
        const start = info.startStr.split('T')[0];
        const end = info.endStr.split('T')[0];
        const rawEvents = await apiGet(`/events?start_date=${start}&end_date=${end}`);
        
        const fcEvents = rawEvents
            .filter(e => activeCalendarIds.has(e.calendar_id))
            .map(e => ({
                id: e.id,
                title: e.title,
                start: e.start_time,
                end: e.end_time,
                allDay: e.is_all_day,
                backgroundColor: e.calendar_color,
                borderColor: e.calendar_color,
                extendedProps: {
                    calendar_id: e.calendar_id,
                    description: e.description,
                    location: e.location,
                    permission_level: e.permission_level,
                    cliente_id: e.cliente_id,
                    cliente_nome: e.cliente_nome,
                    cliente_telefone: e.cliente_telefone,
                    shared_with: e.shared_with
                },
                editable: e.permission_level !== 'read'
            }));
            
        successCallback(fcEvents);
    } catch (e) {
        console.error("Erro ao buscar eventos", e);
        failureCallback(e);
    }
}

function handleDateSelect(info) {
    document.getElementById('event-modal-title').textContent = 'Novo Evento';
    document.getElementById('event-id').value = '';
    document.getElementById('event-title').value = '';
    document.getElementById('event-start').value = info.startStr.slice(0,16);
    document.getElementById('event-end').value = info.endStr.slice(0,16);
    document.getElementById('event-allday').checked = info.allDay;
    document.getElementById('event-location').value = '';
    document.getElementById('event-desc').value = '';
    
    removeClientLink();
    document.getElementById('event-shared-info').style.display = 'none';
    document.getElementById('event-shared-list').innerHTML = '';
    document.getElementById('btn-delete-event').style.display = 'none';
    document.getElementById('btn-save-event').style.display = 'block';
    
    // Desmarcar todos os usuários
    document.querySelectorAll('.share-user-checkbox').forEach(cb => {
        cb.checked = false;
        const id = cb.id.replace('share-user-', '');
        const permSelect = document.getElementById(`share-perm-${id}`);
        if (permSelect) {
            permSelect.value = 'read';
            permSelect.disabled = true;
        }
    });
    
    currentEventId = null;
    currentEventPerm = 'admin'; // Assumindo que criará em um dele
    
    document.getElementById('modal-event').style.display = 'flex';
}

function handleEventClick(info) {
    const e = info.event;
    const props = e.extendedProps;
    
    document.getElementById('event-modal-title').textContent = 'Editar Evento';
    document.getElementById('event-id').value = e.id;
    document.getElementById('event-title').value = e.title;
    document.getElementById('event-calendar').value = props.calendar_id;
    
    const formatDt = (dt) => {
        if (!dt) return '';
        const tzOffset = (new Date()).getTimezoneOffset() * 60000;
        return (new Date(dt - tzOffset)).toISOString().slice(0,16);
    };
    
    document.getElementById('event-start').value = formatDt(e.start);
    document.getElementById('event-end').value = formatDt(e.end || e.start);
    document.getElementById('event-allday').checked = e.allDay;
    document.getElementById('event-location').value = props.location || '';
    document.getElementById('event-desc').value = props.description || '';
    
    if (props.cliente_id) {
        document.getElementById('event-client-id').value = props.cliente_id;
        document.getElementById('client-info-name').textContent = props.cliente_nome || '-';
        document.getElementById('client-info-phone').textContent = props.cliente_telefone || '-';
        document.getElementById('event-client-info').style.display = 'block';
        document.getElementById('event-client-search').parentElement.style.display = 'none';
    } else {
        removeClientLink();
    }
    
    // Preencher as checkboxes com quem já está compartilhado e listar na box apenas se readonly
    document.querySelectorAll('.share-user-checkbox').forEach(cb => {
        cb.checked = false;
        const id = cb.id.replace('share-user-', '');
        const permSelect = document.getElementById(`share-perm-${id}`);
        if (permSelect) {
            permSelect.value = 'read';
            permSelect.disabled = true;
        }
    });
    
    if (props.shared_with && props.shared_with.length > 0) {
        props.shared_with.forEach(s => {
            const cb = Array.from(document.querySelectorAll('.share-user-checkbox')).find(c => c.value === s.email);
            if (cb) {
                cb.checked = true;
                const id = cb.id.replace('share-user-', '');
                const permSelect = document.getElementById(`share-perm-${id}`);
                if (permSelect) {
                    permSelect.value = s.permission_level;
                    permSelect.disabled = false;
                }
            }
        });
        
        if (currentEventPerm === 'read') {
            document.getElementById('event-shared-info').style.display = 'block';
            const listEl = document.getElementById('event-shared-list');
            listEl.innerHTML = '';
            props.shared_with.forEach(s => {
                const li = document.createElement('li');
                li.textContent = `${s.email} (${s.permission_level})`;
                listEl.appendChild(li);
            });
        } else {
            document.getElementById('event-shared-info').style.display = 'none';
        }
    } else {
        document.getElementById('event-shared-info').style.display = 'none';
    }
    
    currentEventId = e.id;
    currentEventPerm = props.permission_level;
    
    const canEdit = currentEventPerm !== 'read';
    document.getElementById('btn-save-event').style.display = canEdit ? 'block' : 'none';
    document.getElementById('btn-delete-event').style.display = canEdit ? 'block' : 'none';
    document.getElementById('event-share-group').style.display = canEdit ? 'block' : 'none';
    
    // Desabilitar inputs se for read-only
    const inputs = document.querySelectorAll('#modal-event input, #modal-event select, #modal-event textarea');
    inputs.forEach(el => el.disabled = !canEdit);
    
    document.getElementById('modal-event').style.display = 'flex';
}

async function handleEventDrop(info) {
    if (info.event.extendedProps.permission_level === 'read') {
        info.revert();
        alert('Você não tem permissão para editar este evento.');
        return;
    }
    
    try {
        await apiPut(`/events/${info.event.id}`, {
            start_time: info.event.start.toISOString(),
            end_time: info.event.end ? info.event.end.toISOString() : info.event.start.toISOString(),
            is_all_day: info.event.allDay
        });
    } catch (e) {
        console.error(e);
        info.revert();
    }
}

function closeModal(id) {
    document.getElementById(id).style.display = 'none';
}

function openNewCalendarModal() {
    document.getElementById('cal-name').value = '';
    document.getElementById('cal-color').value = '#3182CE';
    document.getElementById('modal-new-cal').style.display = 'flex';
}

async function createCalendar() {
    const name = document.getElementById('cal-name').value;
    const color = document.getElementById('cal-color').value;
    if (!name) return alert('Nome é obrigatório');
    
    try {
        await apiPost('/calendars', { name, color });
        closeModal('modal-new-cal');
        await loadCalendars();
    } catch (e) {
        alert('Erro ao criar agenda');
    }
}

async function saveEvent() {
    const sharedUsers = Array.from(document.querySelectorAll('.share-user-checkbox:checked')).map(cb => {
        const id = cb.id.replace('share-user-', '');
        const perm = document.getElementById(`share-perm-${id}`).value;
        return { email: cb.value, permission_level: perm };
    });

    const data = {
        title: document.getElementById('event-title').value,
        calendar_id: document.getElementById('event-calendar').value,
        start_time: new Date(document.getElementById('event-start').value).toISOString(),
        end_time: new Date(document.getElementById('event-end').value).toISOString(),
        is_all_day: document.getElementById('event-allday').checked,
        location: document.getElementById('event-location').value,
        description: document.getElementById('event-desc').value,
        cliente_id: document.getElementById('event-client-id').value ? parseInt(document.getElementById('event-client-id').value) : null,
        shared_with_users: sharedUsers
    };
    
    if (!data.title || !data.calendar_id || !data.start_time || !data.end_time) {
        return alert('Preencha os campos obrigatórios.');
    }
    
    try {
        if (currentEventId) {
            await apiPut(`/events/${currentEventId}`, data);
        } else {
            await apiPost('/events', data);
        }
        closeModal('modal-event');
        calendarInstance.refetchEvents();
    } catch (e) {
        alert('Erro ao salvar evento');
    }
}

async function deleteEvent() {
    if (!confirm('Deseja realmente excluir?')) return;
    try {
        await apiDelete(`/events/${currentEventId}`);
        closeModal('modal-event');
        calendarInstance.refetchEvents();
    } catch (e) {
        alert('Erro ao excluir');
    }
}

function openShareModal(calId) {
    document.getElementById('share-calendar-id').value = calId;
    document.getElementById('share-email').value = '';
    document.getElementById('share-permission').value = 'read';
    document.getElementById('modal-share').style.display = 'flex';
}

async function shareCalendar() {
    const calId = document.getElementById('share-calendar-id').value;
    const email = document.getElementById('share-email').value;
    const perm = document.getElementById('share-permission').value;
    
    if (!email) return alert('E-mail é obrigatório');
    
    try {
        await apiPost(`/calendars/${calId}/share`, { 
            shared_with_email: email,
            permission_level: perm
        });
        closeModal('modal-share');
        alert('Agenda compartilhada com sucesso!');
        await loadCalendars();
    } catch (e) {
        alert('Erro ao compartilhar. O usuário existe?');
    }
}


// --- Cliente Autocomplete ---
let searchTimeout = null;
const searchInput = document.getElementById('event-client-search');
const autocompleteList = document.getElementById('client-autocomplete-list');

if (searchInput) {
    searchInput.addEventListener('input', (e) => {
        clearTimeout(searchTimeout);
        const query = e.target.value.trim();
        if (query.length < 3) {
            autocompleteList.style.display = 'none';
            return;
        }
        searchTimeout = setTimeout(async () => {
            try {
                const token = localStorage.getItem('ordersync_token');
                const baseUrl = window.API_BASE || '';
                const res = await fetch(`${baseUrl}/cliente/lookup?query=${encodeURIComponent(query)}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('API Error');
                const results = await res.json();
                renderAutocomplete(results);
            } catch (err) {
                console.error('Erro na busca de clientes', err);
            }
        }, 500);
    });
}

function renderAutocomplete(results) {
    autocompleteList.innerHTML = '';
    if (results.length === 0) {
        autocompleteList.style.display = 'none';
        return;
    }
    results.forEach(cli => {
        const div = document.createElement('div');
        div.className = 'autocomplete-item';
        div.textContent = `${cli.codigo} - ${cli.nome_fantasia || cli.nome_empresarial}`;
        div.onclick = async () => {
            try {
                // Fetch full client details to get ID and phone
                const token = localStorage.getItem('ordersync_token');
                const baseUrl = window.API_BASE || '';
                const res = await fetch(`${baseUrl}/cliente/${cli.codigo}`, {
                    headers: { 'Authorization': `Bearer ${token}` }
                });
                if (!res.ok) throw new Error('API Error');
                const fullCli = await res.json();
                document.getElementById('event-client-id').value = fullCli.cadastrocliente.id;
                document.getElementById('client-info-name').textContent = fullCli.cadastrocliente.nome_cliente || fullCli.cadastrocliente.nome_fantasia || '-';
                document.getElementById('client-info-phone').textContent = (fullCli.responsavel_compras && fullCli.responsavel_compras.celular_responsavel) ? fullCli.responsavel_compras.celular_responsavel : ((fullCli.representante_legal && fullCli.representante_legal.celular_RepresentanteLegal) ? fullCli.representante_legal.celular_RepresentanteLegal : '-');
                
                document.getElementById('event-client-info').style.display = 'block';
                searchInput.parentElement.style.display = 'none';
                autocompleteList.style.display = 'none';
                searchInput.value = '';
            } catch (err) {
                alert('Erro ao buscar detalhes do cliente.');
            }
        };
        autocompleteList.appendChild(div);
    });
    autocompleteList.style.display = 'block';
}

function removeClientLink() {
    document.getElementById('event-client-id').value = '';
    document.getElementById('client-info-name').textContent = '';
    document.getElementById('client-info-phone').textContent = '';
    document.getElementById('event-client-info').style.display = 'none';
    if(searchInput) {
        searchInput.parentElement.style.display = 'block';
        searchInput.value = '';
    }
}

document.addEventListener('click', (e) => {
    if (autocompleteList && !autocompleteList.contains(e.target) && e.target !== searchInput) {
        autocompleteList.style.display = 'none';
    }
});

// --- Compartilhar Evento ---
function openShareEventModal() {
    if (!currentEventId) return;
    document.getElementById('share-event-email').value = '';
    document.getElementById('share-event-permission').value = 'read';
    document.getElementById('modal-share-event').style.display = 'flex';
}

async function shareEventSubmit() {
    if (!currentEventId) return;
    const email = document.getElementById('share-event-email').value;
    const perm = document.getElementById('share-event-permission').value;
    
    if (!email) return alert('E-mail é obrigatório');
    
    try {
        await apiPost(`/events/${currentEventId}/share`, { 
            shared_with_email: email,
            permission_level: perm
        });
        closeModal('modal-share-event');
        alert('Evento compartilhado com sucesso!');
    } catch (e) {
        alert('Erro ao compartilhar. O usuário existe ou você não tem permissão?');
    }
}
