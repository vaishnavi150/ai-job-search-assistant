import { useAuth } from '../context/AuthContext';

export default function NavBar() {
  const { email, logout } = useAuth();
  return (
    <header className="navbar">
      <span className="brand">AI Job Search Assistant</span>
      {email && (
        <div className="navbar-right">
          <span className="user-email">{email}</span>
          <button className="btn-link" onClick={logout}>Log out</button>
        </div>
      )}
    </header>
  );
}
