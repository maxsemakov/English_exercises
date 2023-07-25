
const form = document.getElementById('uploadForm');
const progressBar = document.getElementById('progressBar');
const statusDiv = document.getElementById('status');

form.addEventListener('submit', (event) => {
  event.preventDefault();
  statusDiv.innerHTML = 'Uploading file...';
  const xhr = new XMLHttpRequest();
  xhr.open('POST', '/upload');
  xhr.upload.onprogress = (event) => {
    const percent = Math.round((event.loaded / event.total) * 100);
    progressBar.firstElementChild.style.width = percent + '%';
  };
  xhr.onload = () => {
    statusDiv.innerHTML = 'Processing file...';
    setTimeout(() => {
      statusDiv.innerHTML = 'File processed successfully';
      progressBar.firstElementChild.style.width = '0%';
    }, 3000);
  };
  xhr.send(new FormData(form));
});