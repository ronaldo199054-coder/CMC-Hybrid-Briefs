// Copy this file to firebase-config.js and fill in your own Firebase
// project values (Firebase console -> Project settings -> Your apps -> Web).
// firebase-config.js is git-ignored: NEVER commit it, and never put an
// App Check debug token, a service-account key, or any secret in the repo.
// The apiKey here is a public web-app identifier, not a private secret;
// access is enforced by Firebase App Check + Firebase AI Logic rules.
//
// Optional fields:
//   appCheckDebugToken: true   -> local development only. Sets
//     self.FIREBASE_APPCHECK_DEBUG_TOKEN so App Check accepts a debug
//     token. Register the printed token in the Firebase console, and
//     remove this before any public deployment.
//   recaptchaSiteKey: "..."    -> reCAPTCHA v3 site key for App Check
//     in production (get it in the Firebase console -> App Check).

export const firebaseConfig = {
  apiKey: "YOUR_API_KEY",
  authDomain: "YOUR_PROJECT.firebaseapp.com",
  projectId: "YOUR_PROJECT_ID",
  storageBucket: "YOUR_PROJECT.appspot.com",
  messagingSenderId: "YOUR_SENDER_ID",
  appId: "YOUR_APP_ID",
  // Cloud model used for the deep brief (Firebase AI Logic, Gemini API backend).
  cloudModel: "gemini-3.5-flash-lite",
  // appCheckDebugToken: true,
  // recaptchaSiteKey: "",
};
