import React from 'react';

function Header({ onNavigate }) {
  return (
    <header className="header">
        <title>ORIA</title>
      <div className="logo" onClick={() => onNavigate('upload')}>ORIA</div>
      <div className="nav-link" onClick={() => onNavigate('about')}>About Us</div>
    </header>
  );
}

export default Header;