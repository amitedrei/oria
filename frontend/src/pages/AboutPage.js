import React from 'react';
import { Instagram } from 'lucide-react';

function AboutPage({ onNavigate }) {
  return (
    <div className="card">
      <h2 className="section-title">Vision</h2>
      <section className="section">
        <div className="divider">
            <p>
            Our mission is to provide innovative solutions that empower businesses
            and individuals alike. We believe in the power of technology to transform
            lives, and we strive to make that vision a reality every day.
            </p>
        </div>
      </section>
      
      <section className="section">
        <h2 className="section-title">How does it work</h2>
        <div className="divider">
            <p>
            Our system detects songs by analyzing images for visual cues like album covers or artists and interpreting any provided text such as lyrics or captions. It then uses AI to match this combined information with a music database to identify the most likely song and display its title, artist, and details.
            </p>
        </div>
      </section>
      
      <section className="section">
        <h2 className="section-title">Credits</h2>
        <div className="divider">
            <p>
                Omer W. <br/>
                Reut K. <br/>
                Itay K. <br/>
                Amit E.
            </p>
        </div>
      </section>
      
      <div className="support-section">
        <div className="support-button">
          <span>SUPPORT US</span>
          <Instagram size={20} />
        </div>
      </div>
    </div>
  );
}

export default AboutPage;