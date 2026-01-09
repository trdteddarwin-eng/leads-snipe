// Import the functions you need from the SDKs you need
import { initializeApp } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-app.js";
import { getAuth, GoogleAuthProvider, signInWithPopup, onAuthStateChanged, signOut } from "https://www.gstatic.com/firebasejs/10.7.1/firebase-auth.js";

// Your web app's Firebase configuration
const firebaseConfig = {
    apiKey: "AIzaSyBG8Mx0iQHC6SJPJ5RVO_cUxqZinP5jdH0",
    authDomain: "leadsnipe-b2708.firebaseapp.com",
    projectId: "leadsnipe-b2708",
    storageBucket: "leadsnipe-b2708.firebasestorage.app",
    messagingSenderId: "221826865514",
    appId: "1:221826865514:web:b9c55dadb78833632bed13",
    measurementId: "G-SPD5MR53H4"
};

// Initialize Firebase
const app = initializeApp(firebaseConfig);
const auth = getAuth(app);
const googleProvider = new GoogleAuthProvider();

export { auth, googleProvider, signInWithPopup, onAuthStateChanged, signOut };
