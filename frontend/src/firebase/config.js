import { initializeApp } from 'firebase/app';
import { getFirestore } from 'firebase/firestore';

const firebaseConfig = {
    apiKey: "AIzaSyAXizydmFiuI4zgoUpEUBPBtEAUSELRNyE",
    authDomain: "corded-key-454317-i8.firebaseapp.com",
    projectId: "corded-key-454317-i8",
    storageBucket: "corded-key-454317-i8.firebasestorage.app",
    messagingSenderId: "929994679306",
    appId: "1:929994679306:web:06d539732d95f9794f2bf3",
    measurementId: "G-PSM9L5PE05"
  };

// Initialize Firebase
const app = initializeApp(firebaseConfig);
export const db = getFirestore(app);