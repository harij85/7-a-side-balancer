import { initInfiniteScroll } from './infinite_scroll.js';

initInfiniteScroll({
  endpoint: "/api/players",
  containerId: "playerList",
  perPage: 14,
  renderItem: (p) => {
    const div = document.createElement("div");
    div.className = "list-group-item d-flex justify-content-between align-items-center flex-wrap";
    div.innerHTML = `
      <div>
        <strong>${p.name}</strong> (${p.position})
        ${p.is_captain ? '<span class="badge bg-primary"><i class="bi bi-person-check-fill"></i> Captain</span>' : ''}
        <br>
        <small>Rating: ${p.skill_rating} | Code: ${p.access_code} | Avail:
          <span class="fw-bold text-${p.available ? 'success' : 'secondary'}">
            ${p.available ? 'Yes' : 'No'}
          </span>
        </small>
      </div>
      <div class="d-flex gap-1 mt-2 mt-sm-0 flex-wrap">
        <form action="/admin/assign_captain/${p.id}" method="POST">
          <button class="btn btn-sm ${p.is_captain ? 'btn-dark' : 'btn-outline-dark'}">${p.is_captain ? 'Unassign' : 'Assign'} Cap</button>
        </form>
        <a href="/profile/${p.id}" class="btn btn-sm btn-outline-info">Profile</a>
        <form action="/admin/remove_player/${p.id}" method="POST">
          <button class="btn btn-sm btn-outline-danger">Remove</button>
        </form>
        <!-- Share Dropdown -->
      <div class="dropdown d-inline">
        <button class="btn btn-sm btn-outline-secondary dropdown-toggle" type="button" data-bs-toggle="dropdown">
          <i class="bi bi-share"></i> Share
        </button>
        <ul class="dropdown-menu">
          <li>
            <a class="dropdown-item" target="_blank"
              href="https://wa.me/?text=Log%20your%20match%20stats%20at:%20${encodeURIComponent(window.location.origin + '/player_login')}%0AUse%20Name:%20${encodeURIComponent(p.name)}%0AAccess%20code:%20${p.access_code}">
              <i class="bi bi-whatsapp"></i> WhatsApp
            </a>
          </li>
          <li>
            <a class="dropdown-item"
              href="mailto:?subject=Log%20Your%207-a-side%20Stats&body=Login:%20${encodeURIComponent(window.location.origin + '/player_login')}%0AName:%20${encodeURIComponent(p.name)}%0ACode:%20${p.access_code}">
              <i class="bi bi-envelope"></i> Email
            </a>
          </li>
          <li><hr class="dropdown-divider"></li>
          <li>
            <button class="dropdown-item" onclick="navigator.clipboard.writeText('Name: ${p.name}\\nCode: ${p.access_code}\\nLink: ${window.location.origin}/player_login'); alert('Login info copied!')">
              <i class="bi bi-clipboard"></i> Copy
            </button>
          </li>
        </ul>
      </div>
      </div>
    `;
    return div;
  }
});
