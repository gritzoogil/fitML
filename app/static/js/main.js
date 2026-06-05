import { initializeApp } from "https://www.gstatic.com/firebasejs/12.14.0/firebase-app.js";
import { getAuth, createUserWithEmailAndPassword, signInWithEmailAndPassword } from "https://www.gstatic.com/firebasejs/12.14.0/firebase-auth.js";

const configEl = document.getElementById('firebase-config');
const firebaseConfig = configEl ? JSON.parse(configEl.textContent) : null;
const app = configEl ? initializeApp(firebaseConfig) : null;
const auth = app ? getAuth(app) : null;

window.handleLogin = async function() {
    if (!auth) return;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    try {
        const result = await signInWithEmailAndPassword(auth, email, password);
        const idToken = await result.user.getIdToken();
        const res = await fetch('/auth/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken })
        });
        const data = await res.json();
        if (data.success) window.location.href = '/dashboard';
        else alert(data.error);
    } catch (err) {
        alert(err.message);
    }
}

window.handleRegister = async function() {
    if (!auth) return;
    const email = document.getElementById('email').value;
    const password = document.getElementById('password').value;
    const confirm = document.getElementById('confirm-password').value;
    if (password !== confirm) return alert('Passwords do not match');
    try {
        const result = await createUserWithEmailAndPassword(auth, email, password);
        const idToken = await result.user.getIdToken();
        const res = await fetch('/auth/verify', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ idToken })
        });
        const data = await res.json();
        if (data.success) window.location.href = '/dashboard';
        else alert(data.error);
    } catch (err) {
        alert(err.message);
    }
}

document.addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
        if (window.location.pathname === '/auth/login') handleLogin();
        if (window.location.pathname === '/auth/register') handleRegister();
    }
});