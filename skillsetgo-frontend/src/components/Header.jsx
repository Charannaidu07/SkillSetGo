import React from 'react';
import './Header.css';

function Header() {
  return (
    <nav className="header-nav">
      <div className="header-container">
        <a className="header-logo" href="#">SkillSetGo</a>
        <button className="header-toggle">
          <span className="toggle-icon">☰</span>
        </button>
        <div className="header-menu">
          <ul className="header-links">
            <li className="header-item">
              <a className="header-link active" href="#">Home</a>
            </li>
            <li className="header-item">
              <a className="header-link" href="#">Find Worker</a>
            </li>
            <li className="header-item dropdown">
              <a className="header-link dropdown-toggle" href="#">
                Register
              </a>
              <ul className="dropdown-menu">
                <li><a className="dropdown-item" href="#">As User</a></li>
                <li><a className="dropdown-item" href="#">As Worker</a></li>
                <li><div className="dropdown-divider"></div></li>
                <li><a className="dropdown-item" href="#">Admin Login</a></li>
              </ul>
            </li>
          </ul>
          <form className="header-search">
            <input type="search" placeholder="Search" className="search-input"/>
            <button type="submit" className="search-button">Search</button>
          </form>
        </div>
      </div>
    </nav>
  );
}

export default Header;