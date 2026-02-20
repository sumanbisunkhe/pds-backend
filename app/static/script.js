const photoWall = document.getElementById("photo-wall");
let photoTrack = document.getElementById("photo-track");

// Track known photos to detect new arrivals
let knownPhotoUrls = new Set();
let currentIndex = 0;
let carouselInterval = null;
let allPhotoItems = [];

async function fetchStats() {
  try {
    const response = await fetch("/api/stats");
    const data = await response.json();
    document.getElementById("stat-total-photos").textContent = data.total_photos;
    document.getElementById("stat-faces").textContent = data.total_encodings;
    document.getElementById("stat-users").textContent = data.total_users;
  } catch (error) {
    console.error("Failed to fetch stats:", error);
  }
}

function startCarousel() {
  if (carouselInterval) clearInterval(carouselInterval);
  carouselInterval = setInterval(() => {
    if (allPhotoItems.length <= 4) return;

    currentIndex++;

    // Loop back smoothly
    if (currentIndex > allPhotoItems.length - 4) {
      currentIndex = 0;
    }

    const itemWidth = allPhotoItems[0].offsetWidth + 16; // 16px gap
    photoTrack.style.transform = `translateX(-${currentIndex * itemWidth}px)`;
  }, 3000);
}

async function fetchPhotoWall() {
  try {
    const response = await fetch("/api/recent-photos");
    const photos = await response.json();

    if (!photos || photos.length === 0) return;

    // Remove empty state if present
    const emptyState = photoTrack.querySelector(".empty-state");
    if (emptyState) emptyState.remove();

    // Find new photos not yet displayed
    const newPhotos = photos.filter(p => !knownPhotoUrls.has(p.url));

    // Reverse to process oldest-first so that prepending puts newest at the absolute front
    newPhotos.reverse().forEach((photo, index) => {
      knownPhotoUrls.add(photo.url);

      const item = document.createElement("div");
      item.className = "photo-item";
      item.style.animationDelay = `${index * 0.1}s`;

      const img = document.createElement("img");
      img.src = photo.url;
      img.alt = "Event Photo";
      img.loading = "lazy";

      // NEW badge
      const badge = document.createElement("span");
      badge.textContent = "NEW";
      badge.style.cssText = `
        position: absolute; top: 10px; right: 10px; z-index: 10;
        background: var(--primary); color: white;
        font-size: 0.6rem; font-weight: 700; letter-spacing: 0.08em;
        padding: 0.2rem 0.5rem; border-radius: 99px;
        box-shadow: 0 0 12px var(--primary-glow);
        transition: opacity 1s ease;
      `;

      item.appendChild(img);
      item.appendChild(badge);

      // Prepend so newest is first (at the left)
      photoTrack.prepend(item);
      allPhotoItems.unshift(item);

      // Fade out badge after 5 seconds
      setTimeout(() => { badge.style.opacity = "0"; }, 5000);
    });

    // Start or restart carousel if we have photos
    if (allPhotoItems.length > 0) {
      startCarousel();
    }

  } catch (error) {
    console.error("Failed to fetch photo wall:", error);
  }
}

// Initial Load
fetchStats();
fetchPhotoWall();
checkWebRegistration();

// Poll every 5 seconds for new photos
setInterval(() => {
  fetchStats();
  fetchPhotoWall();
  
  // Also refresh personal photos periodically if registered
  if (localStorage.getItem('web_id')) {
    fetchMyPhotos();
  }
}, 5000);

// Track downloaded photos to prevent duplicates
let downloadedUrls = new Set(JSON.parse(localStorage.getItem('downloaded_urls') || '[]'));

function saveDownloadedUrls() {
  localStorage.setItem('downloaded_urls', JSON.stringify([...downloadedUrls]));
}

// --- PWA & Web Registration Logic ---

function switchMainTab(tabId) {
  // Update buttons
  document.querySelectorAll('.nav-btn').forEach(btn => {
    btn.classList.remove('active');
  });
  event.currentTarget.classList.add('active');

  // Update content
  document.querySelectorAll('.main-tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.getElementById(`${tabId}-section`).classList.add('active');

  // If switching to my-photos, refresh them
  if (tabId === 'my-photos' && localStorage.getItem('web_id')) {
    fetchMyPhotos();
  }
}

function switchTab(tabName) {
  // Update buttons
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.classList.remove('active');
    if (btn.innerText.toLowerCase().includes(tabName)) {
      btn.classList.add('active');
    }
  });

  // Update content
  document.querySelectorAll('.tab-content').forEach(content => {
    content.classList.remove('active');
  });
  document.getElementById(`${tabName}-tab`).classList.add('active');
}

function handleSelfieSelect(event) {
  const file = event.target.files[0];
  if (!file) return;

  const reader = new FileReader();
  reader.onload = function(e) {
    const dataUrl = e.target.result;
    // Update the compact avatar preview
    const preview = document.getElementById('selfie-preview');
    preview.innerHTML = `<img src="${dataUrl}" alt="Selfie">`;
    preview.classList.add('has-image');
    // Persist for after registration
    localStorage.setItem('selfie_preview', dataUrl);
    document.getElementById('register-btn').disabled = false;
  };
  reader.readAsDataURL(file);
}

async function registerUser() {
  const fileInput = document.getElementById('selfie-input');
  const registerBtn = document.getElementById('register-btn');
  
  if (!fileInput.files[0]) return;

  registerBtn.disabled = true;
  registerBtn.innerText = 'Registering...';

  const formData = new FormData();
  formData.append('file', fileInput.files[0]);
  
  // If we already have a web_id, reuse it to update encoding
  const existingId = localStorage.getItem('web_id');
  if (existingId) {
    formData.append('web_id', existingId);
  }

  try {
    const response = await fetch('/api/register-web', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    if (data.error) {
      alert(data.error);
      registerBtn.disabled = false;
      registerBtn.innerText = 'Register Me';
    } else {
      localStorage.setItem('web_id', data.web_id);
      showRegisteredState(data.web_id);
      fetchMyPhotos();
      
      // Auto-switch to My Photos tab
      setTimeout(() => {
          const myPhotosBtn = document.querySelector('button[onclick*="my-photos"]');
          if (myPhotosBtn) myPhotosBtn.click();
      }, 500);
    }
  } catch (error) {
    console.error('Registration failed:', error);
    alert('Registration failed. Please check your connection.');
    registerBtn.disabled = false;
    registerBtn.innerText = 'Register Me';
  }
}

function checkWebRegistration() {
  const webId = localStorage.getItem('web_id');
  if (webId) {
    showRegisteredState(webId);
    fetchMyPhotos();
  }
}

function showRegisteredState(webId) {
  document.getElementById('registration-form').style.display = 'none';
  document.getElementById('user-gallery-status').style.display = 'block';
  
  // Show header and content in My Photos tab
  const myPhotosHeader = document.getElementById('my-photos-header');
  if (myPhotosHeader) myPhotosHeader.style.display = 'block';
  
  const displayWebId = document.getElementById('display-web-id');
  if (displayWebId) displayWebId.innerText = webId.substring(0, 16) + '...';
  
  // Update gallery empty state
  const grid = document.getElementById('my-photos-grid');
  if (grid && grid.querySelector('.empty-state')) {
      grid.innerHTML = '<div class="empty-state">Finding your photos... check back in a moment.</div>';
  }

  // Show selfie thumbnail in identity avatars
  const savedSelfie = localStorage.getItem('selfie_preview');
  if (savedSelfie) {
    const avatarEl = document.getElementById('selfie-preview-registered');
    if (avatarEl) avatarEl.innerHTML = `<img src="${savedSelfie}" alt="Your selfie">`;
    
    // Also the one in the register tab
    const avatarIconEl = document.getElementById('selfie-preview-registered-icon');
    if (avatarIconEl) avatarIconEl.innerHTML = `<img src="${savedSelfie}" alt="Your selfie">`;
  }

  // Restore toggle state
  const isAuto = localStorage.getItem('auto_download') === 'true';
  const toggle = document.getElementById('auto-download-toggle');
  if (toggle) toggle.checked = isAuto;
}

function resetRegistration() {
  if (confirm('This will remove your current photo access on this browser. Continue?')) {
    localStorage.removeItem('web_id');
    localStorage.removeItem('auto_download');
    localStorage.removeItem('downloaded_urls');
    localStorage.removeItem('selfie_preview');
    if (typeof downloadedUrls !== 'undefined') downloadedUrls.clear();
    
    document.getElementById('registration-form').style.display = 'block';
    document.getElementById('user-gallery-status').style.display = 'none';
    
    // Hide header in My Photos tab
    const myPhotosHeader = document.getElementById('my-photos-header');
    if (myPhotosHeader) myPhotosHeader.style.display = 'none';
    
    // Reset avatar to placeholder icon
    document.getElementById('selfie-preview').innerHTML = `<svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/></svg>`;
    document.getElementById('register-btn').disabled = true;
    document.getElementById('register-btn').innerText = 'Find My Photos';
    document.getElementById('my-photos-grid').innerHTML = '<div class="empty-state">Please register in the Register tab to see your photos.</div>';
  }
}

function toggleAutoDownload(event) {
  localStorage.setItem('auto_download', event.target.checked);
  if (event.target.checked) {
    fetchMyPhotos(); // Trigger immediate check
  }
}

async function fetchMyPhotos() {
  const webId = localStorage.getItem('web_id');
  if (!webId) return;

  try {
    const response = await fetch(`/api/my-photos?web_id=${webId}`);
    const data = await response.json();

    if (data.photos && data.photos.length > 0) {
      const grid = document.getElementById('my-photos-grid');
      const isAutoDownload = localStorage.getItem('auto_download') === 'true';
      
      grid.innerHTML = '';
      data.photos.forEach((url, index) => {
        // Auto-download if enabled and not already downloaded
        if (isAutoDownload && !downloadedUrls.has(url)) {
          initiateDownload(url);
          downloadedUrls.add(url);
          saveDownloadedUrls();
        }

        const item = document.createElement('div');
        item.className = 'photo-item';
        item.style.animationDelay = `${index * 0.05}s`;
        
        const img = document.createElement('img');
        img.src = url;
        img.onclick = () => window.open(url, '_blank');
        
        // Download Button
        const downloadBtn = document.createElement('button');
        downloadBtn.className = 'download-btn';
        downloadBtn.title = 'Download Photo';
        downloadBtn.innerHTML = `<svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"></path><polyline points="7 10 12 15 17 10"></polyline><line x1="12" y1="15" x2="12" y2="3"></line></svg>`;
        downloadBtn.onclick = (e) => {
          e.stopPropagation();
          initiateDownload(url);
          downloadedUrls.add(url);
          saveDownloadedUrls();
        };
        
        item.appendChild(img);
        item.appendChild(downloadBtn);
        grid.appendChild(item);
      });
    }
  } catch (error) {
    console.error('Failed to fetch personal photos:', error);
  }
}

function initiateDownload(url) {
  // Use Cloudinary's fl_attachment flag to force download
  let downloadUrl = url;
  let fileName = `photo_${Date.now()}_${Math.floor(Math.random() * 1000)}.jpg`;

  if (url.includes('cloudinary.com')) {
    // Force download header via Cloudinary transformation
    downloadUrl = url.replace('/upload/', '/upload/fl_attachment/');
    
    // Attempt to extract the public ID for a nicer filename
    try {
      const parts = url.split('/');
      const lastPart = parts[parts.length - 1];
      if (lastPart.includes('.')) {
        fileName = lastPart;
      }
    } catch (e) {
      // Fallback to timestamp if parsing fails
    }
  }
  
  const link = document.createElement('a');
  link.href = downloadUrl;
  link.download = fileName;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
}

async function downloadAllPhotos() {
  const webId = localStorage.getItem('web_id');
  if (!webId) return;

  const btn = document.getElementById('download-all-btn');
  const originalText = btn.innerText;
  btn.disabled = true;
  btn.innerText = 'Initializing...';

  try {
    const response = await fetch(`/api/my-photos?web_id=${webId}`);
    const data = await response.json();

    if (!data.photos || data.photos.length === 0) {
      alert("No photos found to download.");
      btn.innerText = originalText;
      btn.disabled = false;
      return;
    }

    const zip = new JSZip();
    const folder = zip.folder("my_photos");
    const total = data.photos.length;

    for (let i = 0; i < total; i++) {
        const url = data.photos[i];
        btn.innerText = `Fetching ${i+1}/${total}...`;
        
        try {
            // We use the original URL to fetch the blob
            const imgResponse = await fetch(url);
            const blob = await imgResponse.blob();
            
            // Extract filename or use index
            let fileName = `photo_${i + 1}.jpg`;
            try {
                const parts = url.split('/');
                fileName = parts[parts.length - 1];
            } catch(e) {}
            
            folder.file(fileName, blob);
        } catch (err) {
            console.error(`Failed to fetch ${url}`, err);
        }
    }

    btn.innerText = 'Creating ZIP...';
    const content = await zip.generateAsync({type:"blob"});
    
    btn.innerText = 'Saving...';
    const zipName = `my_event_photos_${Date.now()}.zip`;
    const link = document.createElement('a');
    link.href = URL.createObjectURL(content);
    link.download = zipName;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    btn.innerText = originalText;
    btn.disabled = false;

  } catch (error) {
    console.error('Download all failed:', error);
    alert('Failed to generate ZIP. Try individual downloads.');
    btn.innerText = originalText;
    btn.disabled = false;
  }
}
