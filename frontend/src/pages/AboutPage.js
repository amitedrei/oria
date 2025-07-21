import React from "react";
import FlowDiagram from "../components/FlowDiagram";

function AboutPage({ onNavigate }) {
  return (
    <div className="card">
      <h2 className="section-title">Vision</h2>
      <section className="section">
        <div className="divider">
          <p>
            Every image tells a story and every story deserves the perfect
            soundtrack to bring it to life. No matter the platform, Instagram or
            TikTok - the right music can elevate your content and engage your
            audience like never before. We want to make it effortless to find
            the perfect song that resonates with your message and enhances your
            storytelling.
          </p>
        </div>
      </section>

      <section className="section">
        <h2 className="section-title">How does it work</h2>
        <a
          href="https://github.com/amitedrei/oria/"
          target="_blank"
          rel="noreferrer"
        >
          GitHub Repository
        </a>
        <FlowDiagram />
      </section>

      <section className="section">
        <h2 className="section-title">Credits</h2>
        <div className="divider">
          <p>
            Omer W. <br />
            Reut K. <br />
            Itay K. <br />
            Amit E.
          </p>
        </div>
      </section>
    </div>
  );
}

export default AboutPage;
