import { useState } from "react";
import { Link } from "react-router-dom";

import finalCtaPhoto from "@/assets/marketing/final-cta-photo.jpg";
import { ROUTES } from "@/lib/constants";

export function LandingPage() {
  const [tab, setTab] = useState(1);

  return (
    <>
    <section className="hero" style={{paddingBottom: '0'}}>
      <span className="glow g1"></span><span className="glow g2"></span>
      <div className="wrap hero-grid">
        <div>
          <span className="chip chip-glass" style={{height: '28px', padding: '0 14px'}}>Built specifically for the NCLEX-RN</span>
          <h1>Practice the NCLEX-RN the way <span>the exam actually thinks.</span></h1>
          <p className="sub">NextWise is clinical judgment practice for NCLEX-RN candidates — not memorization drills. Every question starts from a real clinical picture, every answer choice comes with a written rationale, and your performance decides what you practice next.</p>
          <div className="hero-cta">
            <Link className="btn btn-cta btn-lg" to={ROUTES.register}>Start Practicing Free</Link>
            <a className="btn btn-glass btn-lg" href="#demo">See a real question <svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg></a>
          </div>
          <p className="hero-fine">Free to start · No credit card required</p>
        </div>
        <div className="stack">
          <div className="ui">
            <div className="ui-bar"><span className="dot"></span><span className="dot"></span><span className="dot"></span><span className="ui-title">Practice quiz · Question 1 of 5</span></div>
            <div className="q">
              <div className="q-tags">
                <span className="chip chip-out">Cardiovascular</span>
                <span className="chip chip-out">Heart Failure</span>
                <span className="chip chip-tint">Medium</span>
                <span className="chip chip-out" style={{marginLeft: 'auto'}}>MCQ</span>
              </div>
              <div className="scn">68-year-old client, 3 days post-discharge for heart failure exacerbation, presents to the outpatient clinic for a routine follow-up.</div>
              <p className="stem">A client with heart failure reports a weight gain of 3 lbs over the past 2 days. What is the nurse's priority action?</p>
              <div className="opts">
                <label className="opt sel"><span className="rad"><i></i></span><span>Notify the provider</span></label>
                <label className="opt"><span className="rad"></span><span>Restrict the client's fluids to 500 mL/day</span></label>
                <label className="opt"><span className="rad"></span><span>Document the finding and reassess in a week</span></label>
                <label className="opt"><span className="rad"></span><span>Advise the client to elevate their legs</span></label>
              </div>
            </div>
          </div>
          <div className="float mini" style={{right: '-14px', bottom: '6px', width: '238px'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '12px'}}>
              <svg viewBox="0 0 100 100" width="58" height="58">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#eeecf8" strokeWidth="11"/>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="url(#ghero)" strokeWidth="11" strokeLinecap="round" strokeDasharray="263.9" strokeDashoffset="73.9" transform="rotate(-90 50 50)"/>
                    <defs><linearGradient id="ghero" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#4c3ad4"/><stop offset="1" stopColor="#7c3aed"/></linearGradient></defs>
                  </svg>
              <div><div style={{fontFamily: '\'Space Grotesk\'', fontSize: '20px', fontWeight: '700'}}>72%</div><div style={{fontSize: '11.5px', color: 'var(--muted)', marginTop: '2px', lineHeight: '1.4'}}>Exam readiness<br /><span className="note" style={{fontSize: '9.5px'}}>Demo data</span></div></div>
            </div>
          </div>
          <div className="float mini" style={{left: '-20px', bottom: '26px', width: '206px', padding: '12px 14px'}}>
            <div style={{display: 'flex', alignItems: 'center', gap: '9px'}}><span className="mk ok"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span><span style={{fontSize: '12px', fontWeight: '600'}}>Rationale on every option</span></div>
          </div>
        </div>
      </div>
      <div className="trust">
        <div className="wrap trust-in">
          <span><i></i>NCLEX-RN Only</span>
          <span><i></i>Clinical Judgment Focus</span>
          <span><i></i>Rationale On Every Option</span>
          <span><i></i>Tells You What To Practice Next</span>
        </div>
      </div>
    </section>

    <section id="demo" className="band-white">
      <div className="wrap">
        <div className="shead">
          <div><span className="eyebrow">Product demo</span><div className="rule"></div></div>
          <div>
            <h2>See the whole learning loop, not a screenshot</h2>
            <p className="lede">Question, answer, rationale, clinical judgment, performance — the five stages a single NextWise item moves you through. Step through them below.</p>
            <p style={{marginTop: '12px', fontSize: '13px', lineHeight: '1.6', color: 'var(--muted)'}}>[Note: this heart failure MCQ demonstrates the interface. It is a candidate for replacement with an item that shows cues, prioritization, and distractor reasoning together more strongly.]</p>
          </div>
        </div>    <div className="tabs">
          <button type="button" className={tab === 1 ? "tab active" : "tab"} onClick={() => setTab(1)}><b>01</b> Question</button>
          <button type="button" className={tab === 2 ? "tab active" : "tab"} onClick={() => setTab(2)}><b>02</b> Answer</button>
          <button type="button" className={tab === 3 ? "tab active" : "tab"} onClick={() => setTab(3)}><b>03</b> Rationale</button>
          <button type="button" className={tab === 4 ? "tab active" : "tab"} onClick={() => setTab(4)}><b>04</b> Clinical judgment</button>
          <button type="button" className={tab === 5 ? "tab active" : "tab"} onClick={() => setTab(5)}><b>05</b> Performance</button>
        </div>

        <div className="panels">
          <div className={tab === 1 ? "panel active" : "panel"}>
            <div className="demo-grid">
              <div className="ui" style={{boxShadow: 'var(--sh-2)'}}>
                <div className="ui-bar"><span className="dot"></span><span className="dot"></span><span className="dot"></span><span className="ui-title">Practice quiz · Question 1 of 5</span><span className="chip chip-out" style={{marginLeft: 'auto'}}>Timer off</span></div>
                <div className="q"><div className="q-tags">
                <span className="chip chip-out">Cardiovascular</span>
                <span className="chip chip-out">Heart Failure</span>
                <span className="chip chip-tint">Medium</span>
                <span className="chip chip-out" style={{marginLeft: 'auto'}}>MCQ</span>
              </div><div className="scn">68-year-old client, 3 days post-discharge for heart failure exacerbation, presents to the outpatient clinic for a routine follow-up.</div><p className="stem">A client with heart failure reports a weight gain of 3 lbs over the past 2 days. What is the nurse's priority action?</p><div className="opts">
                <label className="opt sel"><span className="rad"><i></i></span><span>Notify the provider</span></label>
                <label className="opt"><span className="rad"></span><span>Restrict the client's fluids to 500 mL/day</span></label>
                <label className="opt"><span className="rad"></span><span>Document the finding and reassess in a week</span></label>
                <label className="opt"><span className="rad"></span><span>Advise the client to elevate their legs</span></label>
              </div></div>
              </div>
              <div className="side">
                <div className="side-card"><h4>A clinical picture first</h4><p>Each item opens with the client, the timeline, and the findings — the cues you have to recognize before you can answer. The scenario is part of the question, not decoration.</p></div>
                <div className="side-card"><h4>Tagged before you see it</h4><p>Nursing system, topic, NCLEX category, difficulty, and question type are attached to every item, which is what makes filtering and reporting exact.</p></div>
                <div className="side-card"><h4>Your pace or exam pace</h4><p>The timer is configurable per session. Sessions save automatically, so you can stop mid-quiz and resume.</p></div>
              </div>
            </div>
          </div>

          <div className={tab === 2 ? "panel active" : "panel"}>
            <div className="demo-grid">
              <div className="ui" style={{boxShadow: 'var(--sh-2)'}}>
                <div className="ui-bar"><span className="dot"></span><span className="dot"></span><span className="dot"></span><span className="ui-title">Answer submitted</span><span className="chip chip-ok" style={{marginLeft: 'auto'}}><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Correct</span></div>
                <div className="q"><div className="q-tags">
                <span className="chip chip-out">Cardiovascular</span>
                <span className="chip chip-out">Heart Failure</span>
                <span className="chip chip-tint">Medium</span>
                <span className="chip chip-out" style={{marginLeft: 'auto'}}>MCQ</span>
              </div><p className="stem">A client with heart failure reports a weight gain of 3 lbs over the past 2 days. What is the nurse's priority action?</p><div className="opts">
                <div className="opt ok"><span className="mk ok"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span><span>Notify the provider</span><span className="chip chip-ok" style={{marginLeft: 'auto'}}>Your answer · correct</span></div>
                <div className="opt no"><span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span><span>Restrict the client's fluids to 500 mL/day</span></div>
                <div className="opt no"><span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span><span>Document the finding and reassess in a week</span></div>
                <div className="opt no"><span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span><span>Advise the client to elevate their legs</span></div>
              </div></div>
              </div>
              <div className="side">
                <div className="side-card"><h4>Every option is marked, not just yours</h4><p>You see which choice was correct and which were not, in one view — so a lucky guess and a reasoned answer do not look the same.</p></div>
                <div className="callout"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/><path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2Z"/><path d="m9 10 2 2 4-4"/></svg><div><h4>The rationale opens next</h4><p>Feedback and reasoning arrive together, immediately after you submit.</p></div></div>
              </div>
            </div>
          </div>

          <div className={tab === 3 ? "panel active" : "panel"}>
            <div className="demo-grid">
              <div className="ui" style={{boxShadow: 'var(--sh-2)'}}>
                <div className="ui-bar"><span className="dot"></span><span className="dot"></span><span className="dot"></span><span className="ui-title">Rationale · all four options</span></div>
                <div style={{padding: '18px'}} className="rat">
                <div className="rrow ok">
                  <span className="mk ok"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span>
                  <div>
                    <div style={{display: 'flex', alignItems: 'baseline', gap: '9px', flexWrap: 'wrap'}}><span className="ropt">Notify the provider</span><span className="rtag ok">Correct</span></div>
                    <p className="rwhy">A 3 lb gain in 2 days signals fluid retention and worsening heart failure. Reporting it lets the provider adjust therapy before the client decompensates. Recognizing the cue and escalating is the priority action.</p>
                  </div>
                </div>
                <div className="rrow">
                  <span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span>
                  <div>
                    <div style={{display: 'flex', alignItems: 'baseline', gap: '9px', flexWrap: 'wrap'}}><span className="ropt">Restrict the client's fluids to 500 mL/day</span><span className="rtag">Incorrect</span></div>
                    <p className="rwhy">Fluid restriction requires a provider order, and 500 mL/day is well below typical heart failure limits. Acting independently here is outside nursing scope.</p>
                  </div>
                </div>
                <div className="rrow">
                  <span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span>
                  <div>
                    <div style={{display: 'flex', alignItems: 'baseline', gap: '9px', flexWrap: 'wrap'}}><span className="ropt">Document the finding and reassess in a week</span><span className="rtag">Incorrect</span></div>
                    <p className="rwhy">Documentation alone delays treatment. A week of unaddressed fluid gain risks pulmonary edema.</p>
                  </div>
                </div>
                <div className="rrow">
                  <span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span>
                  <div>
                    <div style={{display: 'flex', alignItems: 'baseline', gap: '9px', flexWrap: 'wrap'}}><span className="ropt">Advise the client to elevate their legs</span><span className="rtag">Incorrect</span></div>
                    <p className="rwhy">Leg elevation may ease peripheral edema but does not address systemic fluid overload or the need for provider review.</p>
                  </div>
                </div>
                </div>
              </div>
              <div className="side">
                <div className="side-card"><h4>Where students actually lose points</h4><p>Rarely because an option is absurd — usually because a reasonable action is not the priority action. Naming that distinction, option by option, is what the rationale is for.</p></div>
                <div className="side-card"><h4>Plain clinical language</h4><p>Written by nursing educators, in the language you would use on the floor rather than textbook phrasing.</p></div>
              </div>
            </div>
          </div>

          <div className={tab === 4 ? "panel active" : "panel"}>
            <div className="demo-grid">
              <div className="ui" style={{boxShadow: 'var(--sh-2)'}}>
                <div className="ui-bar"><span className="dot"></span><span className="dot"></span><span className="dot"></span><span className="ui-title">Clinical judgment mapping</span></div>
                <div style={{padding: '20px'}}>
                  <span className="note">This item measures</span>
                  <div style={{display: 'flex', flexDirection: 'column', gap: '10px', marginTop: '14px'}}>
                    <div className="callout"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><circle cx="12" cy="12" r="9"/><circle cx="12" cy="12" r="4.5"/><circle cx="12" cy="12" r="1"/></svg><div><h4>Recognize cues</h4><p>A 3 lb gain in 2 days is the finding that matters. Weight trend, not symptom report, is the cue.</p></div></div>
                    <div className="callout"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M9 3a3 3 0 0 0-3 3 3 3 0 0 0-1 5.8V17a4 4 0 0 0 8 0V6a3 3 0 0 0-3-3Z"/><path d="M13 6a3 3 0 0 1 6 0 3 3 0 0 1 1 5.8V17a4 4 0 0 1-7 2.6"/></svg><div><h4>Analyze cues</h4><p>Rapid gain post-discharge points to fluid retention and worsening failure, not a dietary blip.</p></div></div>
                    <div className="callout"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/></svg><div><h4>Take action</h4><p>Escalating to the provider is the action within scope that changes the client's trajectory.</p></div></div>
                  </div>
                  <div style={{marginTop: '18px', display: 'flex', flexWrap: 'wrap', gap: '6px'}}>
                    <span className="chip chip-out">Recognize cues</span><span className="chip chip-out">Analyze cues</span><span className="chip chip-out">Prioritize hypotheses</span><span className="chip chip-out">Generate solutions</span><span className="chip chip-out">Take action</span><span className="chip chip-out">Evaluate outcomes</span>
                  </div>
                </div>
              </div>
              <div className="side">
                <div className="side-card"><h4>Reported by step, not just by topic</h4><p>Because every item is mapped to a step of the clinical judgment model, your results can tell you whether you are missing cues or misprioritizing — two very different problems.</p></div>
                <div className="side-card"><h4>Not affiliated with NCSBN</h4><p>NextWise references the publicly published Clinical Judgment Measurement Model. It is not endorsed by, approved by, or affiliated with NCSBN.</p></div>
              </div>
            </div>
          </div>

          <div className={tab === 5 ? "panel active" : "panel"}>
            <div className="demo-grid">
              <div className="ui" style={{boxShadow: 'var(--sh-2)'}}>
                <div className="ui-bar"><span className="dot"></span><span className="dot"></span><span className="dot"></span><span className="ui-title">Performance after this question</span><span className="demo-flag" style={{marginLeft: 'auto'}}>Demo data</span></div>
                <div style={{padding: '20px'}}>
                  <div className="st3">
                    <div className="st"><b>+1</b><span>Cardiovascular answered</span></div>
                    <div className="st"><b>Medium</b><span>Difficulty passed</span></div>
                    <div className="st"><b>Recognize cues</b><span>Step credited</span></div>
                  </div>
                  <div className="rows" style={{marginTop: '20px'}}><div className="row"><span className="n">Cardiovascular</span><span className="p" style={{color: 'var(--primary)'}}>71%</span><span className="bar"><i style={{width: '71%'}}></i></span></div>
                  <div className="row"><span className="n">Pharmacology</span><span className="p" style={{color: 'var(--warn)'}}>41%</span><span className="bar warn"><i style={{width: '41%'}}></i></span></div>
                  <div className="row"><span className="n">Management of Care</span><span className="p" style={{color: 'var(--primary)'}}>64%</span><span className="bar"><i style={{width: '64%'}}></i></span></div></div>
                  <div className="callout" style={{marginTop: '20px'}}><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/></svg><div><h4>What changes next</h4><p>Pharmacology stays your weakest category, so the next recommended session targets it rather than repeating cardiovascular.</p></div></div>
                </div>
              </div>
              <div className="side">
                <div className="side-card"><h4>One question, four records</h4><p>Every answer updates your category accuracy, subcategory accuracy, difficulty profile, and clinical judgment step — which is what makes the recommendation specific.</p></div>
                <div className="side-card"><h4>Nothing to configure</h4><p>You do not have to audit your own results to notice a pattern. The dashboard names it and turns it into a quiz.</p></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="how">
      <div className="wrap">
        <div className="shead">
          <div><span className="eyebrow">The loop</span><div className="rule"></div></div>
          <div>
            <h2>How NextWise Works</h2>
            <p className="lede">Five steps, repeated. Each pass through tells the platform more about what you should see next.</p>
          </div>
        </div>
        <div className="flow">
          <div className="fstep">
            <span className="fnum">01</span>
            <div className="fnode"><i></i></div>
            <h4>Practice</h4>
            <p>Choose a topic, category, or practice session.</p>
            <div className="fvis"><div style={{display: 'flex', flexDirection: 'column', gap: '7px'}}><span className="chip chip-tint">Pharmacology</span><span className="chip chip-out">Medium</span><span className="chip chip-out">10 questions</span></div></div>
          </div>
          <div className="fstep">
            <span className="fnum">02</span>
            <div className="fnode"><i></i></div>
            <h4>Think clinically</h4>
            <p>Work through NCLEX-RN clinical judgment scenarios in the question types available today.</p>
            <div className="fvis"><div style={{fontSize: '11.5px', lineHeight: '1.5', color: 'var(--muted)'}}><b style={{color: 'var(--ink)'}}>Client, 3 days post-discharge…</b><div style={{marginTop: '8px', height: '6px', borderRadius: '4px', background: '#efedf8'}}></div><div style={{marginTop: '6px', height: '6px', width: '70%', borderRadius: '4px', background: '#efedf8'}}></div></div></div>
          </div>
          <div className="fstep">
            <span className="fnum">03</span>
            <div className="fnode"><i></i></div>
            <h4>Understand why</h4>
            <p>Review detailed rationales for the correct answer and the distractors.</p>
            <div className="fvis"><div style={{display: 'flex', gap: '8px', alignItems: 'flex-start'}}><span className="mk ok"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span><span style={{fontSize: '11.5px', lineHeight: '1.5', color: 'var(--muted)'}}>Correct — recognizing the cue and escalating is the priority.</span></div></div>
          </div>
          <div className="fstep">
            <span className="fnum">04</span>
            <div className="fnode"><i></i></div>
            <h4>Find your weak areas</h4>
            <p>NextWise identifies the areas where you need more practice.</p>
            <div className="fvis"><div className="row" style={{gap: '5px'}}><span className="n" style={{fontSize: '12px'}}>Pharmacology</span><span className="p" style={{fontSize: '11.5px', color: 'var(--warn)'}}>41%</span><span className="bar warn"><i style={{width: '41%'}}></i></span></div></div>
          </div>
          <div className="fstep">
            <span className="fnum">05</span>
            <div className="fnode"><i></i></div>
            <h4>Practice smarter</h4>
            <p>Your performance guides what you practice next.</p>
            <div className="fvis"><div style={{fontSize: '11.5px', lineHeight: '1.5'}}><span className="note" style={{color: 'var(--primary)'}}>Up next</span><p style={{marginTop: '6px'}}>10 questions · Pharmacology</p><div style={{marginTop: '10px', height: '26px', borderRadius: '8px', background: 'linear-gradient(135deg,#5b46e0,#7c3aed)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: '600', fontSize: '11px'}}>Start</div></div></div>
          </div>
        </div>
      </div>
    </section>

    <section id="ngn" className="dark">
      <div className="wrap">
        <div className="shead">
          <div><span className="eyebrow on-dark">Signature · NGN</span><div className="rule" style={{background: 'linear-gradient(90deg,#c4b5fd,#fff)'}}></div></div>
          <div>
            <h2>The exam stopped asking what you remember</h2>
            <p className="lede">The Next Generation NCLEX measures clinical judgment: whether you can recognize the cues that matter, weigh them, act, and evaluate what happened. NextWise questions are written around that sequence — which is the difference between practising judgment and drilling a question bank. What is live today and what is still in development is stated plainly below.</p>
          </div>
        </div>
        <div className="path">
            <div className="pnode hi"><b>01</b><h4>Recognize cues</h4><p>Which findings in the scenario actually matter?</p></div>
            <div className="pnode"><b>02</b><h4>Analyze cues</h4><p>What do those findings mean together?</p></div>
            <div className="pnode"><b>03</b><h4>Prioritize hypotheses</h4><p>Which explanation is most urgent?</p></div>
            <div className="pnode"><b>04</b><h4>Generate solutions</h4><p>What actions are available to you?</p></div>
            <div className="pnode hi"><b>05</b><h4>Take action</h4><p>Which one comes first, and why?</p></div>
            <div className="pnode"><b>06</b><h4>Evaluate outcomes</h4><p>Did the action produce the expected result?</p></div>
        </div>
        <div className="pathline"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M5 12h14M13 6l6 6-6 6"/></svg> <span>Highlighted steps are the ones the heart failure item above measures — each question maps to its own subset.</span></div>
        <div style={{marginTop: '44px', display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', alignItems: 'start'}}>
          <div className="pnode" style={{padding: '24px'}}>
            <h4 style={{fontSize: '18px'}}>From scenario to judgment</h4>
            <p style={{marginTop: '10px', fontSize: '14px', lineHeight: '1.7'}}>A clinical picture arrives with more information than you need. The work is deciding which findings matter, what they mean together, and which action comes first. Every NextWise item is written to make you do that work rather than recognise a keyword.</p>
          </div>
          <div className="pnode" style={{padding: '24px'}}>
            <h4 style={{fontSize: '18px'}}>What is available, and what is not</h4>
            <div className="status">
              <div className="srow live">
                <div><span className="st-title">Clinical judgment practice</span><span className="d">Scenario-based questions written around the six-step reasoning sequence.</span></div>
                <span className="stat-chip on">Available</span>
              </div>
              <div className="srow live">
                <div><span className="st-title">Traditional question types</span><span className="d">Multiple Choice (MCQ) and Select All That Apply (SATA).</span></div>
                <span className="stat-chip on">Available</span>
              </div>
              <div className="srow">
                <div><span className="st-title">NGN item types</span><span className="d">Matrix/Grid, Bow-Tie, Extended Multiple Response, Drag and Drop, Cloze, Enhanced Hot Spot.</span></div>
                <span className="stat-chip off">In development</span>
              </div>
              <div className="srow">
                <div><span className="st-title">NGN case studies</span><span className="d">Unfolding multi-question cases built on a single client scenario.</span></div>
                <span className="stat-chip off">Coming soon</span>
              </div>
            </div>
            <p style={{marginTop: '16px', fontSize: '12.5px', lineHeight: '1.6', color: '#a9a3d6'}}>The six steps above describe the Clinical Judgment Measurement Model as published by NCSBN. NextWise is an independent platform and is not endorsed by, approved by, or affiliated with NCSBN.</p>
          </div>
        </div>
      </div>
    </section>

    <section id="features" className="band-white">
      <div className="wrap">
        <div className="shead">
          <div><span className="eyebrow">Why NextWise</span><div className="rule"></div></div>
          <div>
            <h2>Four differences you can see in the product</h2>
            <p className="lede">Not a feature list. Each of these is something you can point at on a screen.</p>
          </div>
        </div>
        <div className="feat">
            <div>
              <span className="eyebrow">01</span>
              <h3>Judgment, not recall</h3>
              <p className="d">Questions are written from a clinical picture — findings, timing, and priority — so you practice deciding, not remembering.</p>
            </div>
            <div className="vis"><div className="ui" style={{boxShadow: 'var(--sh-1)'}}><div className="q" style={{padding: '16px'}}><div className="q-tags">
                <span className="chip chip-out">Cardiovascular</span>
                <span className="chip chip-out">Heart Failure</span>
                <span className="chip chip-tint">Medium</span>
                <span className="chip chip-out" style={{marginLeft: 'auto'}}>MCQ</span>
              </div><div className="scn">68-year-old client, 3 days post-discharge for heart failure exacerbation, presents to the outpatient clinic for a routine follow-up.</div><p className="stem">A client with heart failure reports a weight gain of 3 lbs over the past 2 days. What is the nurse's priority action?</p></div></div></div>
          </div>
          <div className="feat spot">
            <div>
              <span className="chip chip-tint" style={{height: '26px', padding: '0 12px'}}>02 · Core differentiator</span>
              <h3>Every option explained. Not just right or wrong.</h3>
              <p className="d">You get the reasoning for why the correct answer is correct — and for why each distractor you did not pick is wrong. A grade tells you nothing you can use tomorrow. The reasoning is what transfers to the next question.</p>
              <div className="spot-proof">
                <span className="chip chip-ok">4 of 4 options explained</span>
                <span className="chip chip-out">Written by nursing educators</span>
                <span className="chip chip-out">Shown immediately after you submit</span>
              </div>
            </div>
            <div className="vis"><div className="ui" style={{boxShadow: 'var(--sh-1)'}}><div style={{padding: '16px'}} className="rat"><div className="rrow ok">
                  <span className="mk ok"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg></span>
                  <div>
                    <div style={{display: 'flex', alignItems: 'baseline', gap: '9px', flexWrap: 'wrap'}}><span className="ropt">Notify the provider</span><span className="rtag ok">Correct</span></div>
                    <p className="rwhy">A 3 lb gain in 2 days signals fluid retention and worsening heart failure. Reporting it lets the provider adjust therapy before the client decompensates. Recognizing the cue and escalating is the priority action.</p>
                  </div>
                </div>
                <div className="rrow">
                  <span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span>
                  <div>
                    <div style={{display: 'flex', alignItems: 'baseline', gap: '9px', flexWrap: 'wrap'}}><span className="ropt">Restrict the client's fluids to 500 mL/day</span><span className="rtag">Incorrect</span></div>
                    <p className="rwhy">Fluid restriction requires a provider order, and 500 mL/day is well below typical heart failure limits. Acting independently here is outside nursing scope.</p>
                  </div>
                </div>
                <div className="rrow">
                  <span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span>
                  <div>
                    <div style={{display: 'flex', alignItems: 'baseline', gap: '9px', flexWrap: 'wrap'}}><span className="ropt">Document the finding and reassess in a week</span><span className="rtag">Incorrect</span></div>
                    <p className="rwhy">Documentation alone delays treatment. A week of unaddressed fluid gain risks pulmonary edema.</p>
                  </div>
                </div>
                <div className="rrow">
                  <span className="mk no"><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M18 6 6 18M6 6l12 12"/></svg></span>
                  <div>
                    <div style={{display: 'flex', alignItems: 'baseline', gap: '9px', flexWrap: 'wrap'}}><span className="ropt">Advise the client to elevate their legs</span><span className="rtag">Incorrect</span></div>
                    <p className="rwhy">Leg elevation may ease peripheral edema but does not address systemic fluid overload or the need for provider review.</p>
                  </div>
                </div></div></div></div>
          </div>
          <div className="feat">
            <div>
              <span className="eyebrow">03</span>
              <h3>It tells you what to study next</h3>
              <p className="d">Most question banks hand you a score and leave the plan to you. NextWise reads your weakest category, then queues a specific, sized session on it — so you are never deciding what to study while you study.</p>
            </div>
            <div className="vis"><div className="side-card" style={{boxShadow: 'var(--sh-1)'}}>
            <div style={{display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px'}}><span className="note">Weakest areas</span><span className="demo-flag">Demo data</span></div>
            <div className="rows"><div className="row"><span className="n">Pharmacology</span><span className="p" style={{color: 'var(--warn)'}}>41%</span><span className="bar warn"><i style={{width: '41%'}}></i></span></div>
                  <div className="row"><span className="n">Management of Care</span><span className="p" style={{color: 'var(--primary)'}}>64%</span><span className="bar"><i style={{width: '64%'}}></i></span></div></div>
            <div className="callout" style={{marginTop: '18px'}}><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 3v4M12 17v4M3 12h4M17 12h4M5.6 5.6l2.8 2.8M15.6 15.6l2.8 2.8M18.4 5.6l-2.8 2.8M8.4 15.6l-2.8 2.8"/></svg><div><h4>Recommended next</h4><p>10 questions on Pharmacology, at the difficulty you are missing.</p></div></div>
          </div></div>
          </div>
          <div className="feat rev">
            <div>
              <span className="eyebrow">04</span>
              <h3>Aligned to the exam blueprint</h3>
              <p className="d">Content is organized by NCLEX category and subcategory, and mapped to the six steps of the clinical judgment model.</p>
            </div>
            <div className="vis"><div className="side-card" style={{boxShadow: 'var(--sh-1)'}}>
            <span className="note">Category breakdown</span>
            <div className="rows"><div className="row"><span className="n">Fundamentals</span><span className="p" style={{color: 'var(--primary)'}}>82%</span><span className="bar"><i style={{width: '82%'}}></i></span></div>
                  <div className="row"><span className="n">Safety & Infection Control</span><span className="p" style={{color: 'var(--primary)'}}>74%</span><span className="bar"><i style={{width: '74%'}}></i></span></div>
                  <div className="row"><span className="n">Health Promotion & Maintenance</span><span className="p" style={{color: 'var(--primary)'}}>66%</span><span className="bar"><i style={{width: '66%'}}></i></span></div>
                  <div className="row"><span className="n">Mental Health</span><span className="p" style={{color: 'var(--warn)'}}>58%</span><span className="bar warn"><i style={{width: '58%'}}></i></span></div></div>
            <div style={{marginTop: '18px', display: 'flex', flexWrap: 'wrap', gap: '6px'}}><span className="chip chip-out">Recognize cues</span><span className="chip chip-out">Analyze cues</span><span className="chip chip-out">Prioritize hypotheses</span><span className="chip chip-out">Generate solutions</span><span className="chip chip-tint">+2 more</span></div>
          </div></div>
          </div>
      </div>
    </section>

    <section id="dashboard" className="band-tint">
      <div className="wrap">
        <div className="shead">
          <div><span className="eyebrow">Performance dashboard</span><div className="rule"></div></div>
          <div>
            <h2>It does not just score you. It tells you what to practice next.</h2>
            <p className="lede">Readiness, accuracy, weak areas, clinical judgment performance, and progress over time — all of it feeding one recommendation. Reporting a 41% in Pharmacology is the easy part; turning it into the next session you sit down to is the point.</p>
            <div style={{marginTop: '16px'}}><span className="demo-flag"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 9v4M12 17h.01"/><path d="M10.3 3.9 1.8 18a2 2 0 0 0 1.7 3h17a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0Z"/></svg> All figures below are demo data</span></div>
          </div>
        </div>
        <div className="dash">
          <div className="dash-bar">
            <span className="dot"></span><span className="dot"></span><span className="dot"></span>
            <span className="ui-title">Dashboard · exam readiness</span>
            <span className="demo-flag" style={{marginLeft: 'auto'}}>Demo data</span>
          </div>
          <div className="dash-grid">
            <div style={{display: 'flex', flexDirection: 'column', gap: '18px'}}>
              <div className="tile">
                <div className="tl"><span className="tile-l">Exam readiness</span><span className="dtag">Demo data</span></div>
                <div style={{display: 'flex', alignItems: 'center', gap: '22px', marginTop: '16px'}}>
                  <svg viewBox="0 0 100 100" width="104" height="104">
                    <circle cx="50" cy="50" r="42" fill="none" stroke="#eeecf8" strokeWidth="11"/>
                    <circle cx="50" cy="50" r="42" fill="none" stroke="url(#gdash)" strokeWidth="11" strokeLinecap="round" strokeDasharray="263.9" strokeDashoffset="73.9" transform="rotate(-90 50 50)"/>
                    <defs><linearGradient id="gdash" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stopColor="#4c3ad4"/><stop offset="1" stopColor="#7c3aed"/></linearGradient></defs>
                  </svg>
                  <div>
                    <div className="big">72%</div>
                    <p style={{fontSize: '13.5px', lineHeight: '1.6', color: 'var(--muted)', marginTop: '8px', maxWidth: '230px'}}>Estimated readiness across every category you have practised.</p>
                  </div>
                </div>
                <div className="st3">
                  <div className="st"><b>1,284</b><span>Questions answered</span><span className="dtag">Demo</span></div>
                  <div className="st"><b>68%</b><span>Overall accuracy</span><span className="dtag">Demo</span></div>
                  <div className="st"><b>14</b><span>Day streak</span><span className="dtag">Demo</span></div>
                </div>
              </div>
              <div className="tile">
                <div className="tl"><span className="tile-l">Progress over time</span><span className="dtag">Demo data</span></div>
                <svg viewBox="0 0 320 110" width="100%" height="110" preserveAspectRatio="none" style={{marginTop: '16px', display: 'block'}}>
                  <line x1="0" y1="27.5" x2="320" y2="27.5" stroke="#f1eff9"/><line x1="0" y1="66" x2="320" y2="66" stroke="#f1eff9"/>
                  <polygon fill="rgba(92,70,224,.08)" points="4,88 50,79.2 96,83.6 142,60.50000000000001 188,50.6 234,55 280,33 316,24.2 316,110 4,110"/>
                  <polyline fill="none" stroke="#5c46e0" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" points="4,88 50,79.2 96,83.6 142,60.50000000000001 188,50.6 234,55 280,33 316,24.2"/>
                </svg>
                <div style={{display: 'flex', justifyContent: 'space-between', marginTop: '10px', fontSize: '12px', color: 'var(--muted)'}}><span>8 weeks ago</span><span>This week</span></div>
              </div>
              <div className="tile">
                <div className="tl"><span className="tile-l">Clinical judgment performance</span><span className="dtag">Demo data</span></div>
                <div className="rows"><div className="row"><span className="n">Recognize cues</span><span className="p" style={{color: 'var(--primary)'}}>78%</span><span className="bar"><i style={{width: '78%'}}></i></span></div>
                  <div className="row"><span className="n">Analyze cues</span><span className="p" style={{color: 'var(--primary)'}}>69%</span><span className="bar"><i style={{width: '69%'}}></i></span></div>
                  <div className="row"><span className="n">Prioritize hypotheses</span><span className="p" style={{color: 'var(--warn)'}}>55%</span><span className="bar warn"><i style={{width: '55%'}}></i></span></div>
                  <div className="row"><span className="n">Take action</span><span className="p" style={{color: 'var(--primary)'}}>73%</span><span className="bar"><i style={{width: '73%'}}></i></span></div></div>
              </div>
            </div>
            <div style={{display: 'flex', flexDirection: 'column', gap: '18px'}}>
              <div className="tile">
                <div className="tl"><span className="tile-l">Weakest areas</span><span className="dtag">Demo data</span></div>
                <div className="rows"><div className="row"><span className="n">Pharmacology</span><span className="p" style={{color: 'var(--warn)'}}>41%</span><span className="bar warn"><i style={{width: '41%'}}></i></span></div>
                  <div className="row"><span className="n">Mental Health</span><span className="p" style={{color: 'var(--warn)'}}>52%</span><span className="bar warn"><i style={{width: '52%'}}></i></span></div>
                  <div className="row"><span className="n">Management of Care</span><span className="p" style={{color: 'var(--primary)'}}>64%</span><span className="bar"><i style={{width: '64%'}}></i></span></div>
                  <div className="row"><span className="n">Fundamentals</span><span className="p" style={{color: 'var(--primary)'}}>82%</span><span className="bar"><i style={{width: '82%'}}></i></span></div></div>
              </div>
              <div className="tile" style={{background: 'linear-gradient(140deg,#f2effe,#f7f5ff)', borderColor: 'rgba(92,70,224,.18)'}}>
                <div className="tl"><span className="tile-l" style={{color: 'var(--primary)'}}>Recommended next practice</span><span className="chip chip-tint">The differentiator</span></div>
                <p style={{fontSize: '15px', lineHeight: '1.6', marginTop: '12px'}}>10 questions on <strong>Pharmacology</strong> — your lowest category this week.</p>
                <p style={{fontSize: '12.5px', lineHeight: '1.55', color: 'var(--muted)', marginTop: '8px'}}>Generated from your own results. You do not have to build a study plan yourself.</p>
                <Link className="btn btn-cta" style={{marginTop: '16px', width: '100%'}} to={ROUTES.register}>Practice this area</Link>
              </div>
              <div className="callout"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M3 3v18h18"/><path d="m7 15 4-4 3 3 5-6"/></svg><div><h4>Readiness is an estimate, not a prediction</h4><p>It reflects your accuracy across categories you have practised. It is not a pass guarantee, and no NCLEX pass rate is claimed.</p></div></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <section id="coverage">
      <div className="wrap">
        <div className="shead">
          <div><span className="eyebrow">Coverage</span><div className="rule"></div></div>
          <div>
            <h2>What you can practice today</h2>
            <p className="lede">Only the categories NextWise genuinely has questions for. Nothing here is a roadmap item dressed up as a feature.</p>
          </div>
        </div>
        <div className="cov">
            <div className="cov-card"><span className="chip chip-tint"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 12 10 5 10-5"/><path d="m2 17 10 5 10-5"/></svg> Live</span><h4>Fundamentals</h4><p>Core nursing skills, assessment, and the basics every item builds on.</p></div>
            <div className="cov-card"><span className="chip chip-tint"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 12 10 5 10-5"/><path d="m2 17 10 5 10-5"/></svg> Live</span><h4>Pharmacology</h4><p>Drug classes, administration, adverse effects, and priority nursing implications.</p></div>
            <div className="cov-card"><span className="chip chip-tint"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 12 10 5 10-5"/><path d="m2 17 10 5 10-5"/></svg> Live</span><h4>Mental Health</h4><p>Therapeutic communication, crisis response, and psychosocial priorities.</p></div>
            <div className="cov-card"><span className="chip chip-tint"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 12 10 5 10-5"/><path d="m2 17 10 5 10-5"/></svg> Live</span><h4>Management of Care</h4><p>Delegation, prioritization, advocacy, and continuity of care.</p></div>
            <div className="cov-card"><span className="chip chip-tint"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 12 10 5 10-5"/><path d="m2 17 10 5 10-5"/></svg> Live</span><h4>Safety & Infection Control</h4><p>Precautions, error prevention, handling, and safe environment.</p></div>
            <div className="cov-card"><span className="chip chip-tint"><svg viewBox="0 0 24 24" width="18" height="18" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 2 2 7l10 5 10-5-10-5Z"/><path d="m2 12 10 5 10-5"/><path d="m2 17 10 5 10-5"/></svg> Live</span><h4>Health Promotion & Maintenance</h4><p>Prevention, screening, developmental stages, and self-care teaching.</p></div>
        </div>
        <p className="cov-note">Additional categories are being written by the content team and will appear here as they go live. Within each category you can filter by subcategory, nursing system, difficulty, and question type before you start a session.</p>
      </div>
    </section>

    <section id="pricing" className="band-white">
      <div className="wrap">
        <div className="shead">
          <div><span className="eyebrow">Pricing</span><div className="rule"></div></div>
          <div>
            <h2>Start free. Upgrade when you need the full bank.</h2>
            <p className="lede">Prototype pricing concept. Plans, limits, and prices are not final and will be published before launch.</p>
          </div>
        </div>
        <div className="price">
          <div className="pcard">
            <h3>Free</h3>
            <div className="pprice">Free to start</div>
            <p className="pnote">No credit card required</p>
            <ul className="plist">
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Limited practice</li>
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Basic performance tracking</li>
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Clinical judgment practice questions</li>
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Rationales on the questions included</li>
            </ul>
            <div className="pfoot"><Link className="btn btn-quiet btn-lg" style={{width: '100%'}} to={ROUTES.register}>Start Practicing Free</Link></div>
          </div>
          <div className="pcard pro">
            <div style={{position: 'relative', display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '12px'}}>
              <h3>Premium</h3>
              <span className="chip chip-glass">Full platform</span>
            </div>
            <div className="pprice">Pricing coming soon</div>
            <p className="pnote">Plan limits and price to be confirmed before launch</p>
            <ul className="plist">
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Unlimited practice</li>
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> NGN item types <span className="stat-chip off" style={{marginLeft: '6px'}}>When released</span></li>
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Detailed rationales on every option</li>
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Personalized practice recommendations</li>
              <li><svg viewBox="0 0 24 24" width="16" height="16" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><path d="M20 6 9 17l-5-5"/></svg> Full performance analytics</li>
            </ul>
            <div className="pfoot"><Link className="btn btn-lg" style={{width: '100%', background: '#fff', color: 'var(--primary)'}} to={ROUTES.register}>Notify me at launch</Link></div>
          </div>
        </div>
      </div>
    </section>

    <section id="faq">
      <div className="wrap">
        <div className="shead">
          <div><span className="eyebrow">FAQ</span><div className="rule"></div></div>
          <div>
            <h2>Questions students ask first</h2>
            <p className="lede">Answers describe the product as it exists today. Anything in build is labelled as such.</p>
          </div>
        </div>
        <div className="faq">
          <details open><summary>Is NextWise for the NCLEX-RN?</summary><p>Yes — NextWise is built specifically for NCLEX-RN candidates. It is not a general nursing-exam bank. NCLEX-PN is not part of the current product and may be added later.</p></details>
          <details><summary>Does NextWise include NGN practice?</summary><p>NextWise focuses on clinical judgment practice, which is what the Next Generation NCLEX measures. Available today: scenario-based clinical judgment questions in Multiple Choice and Select All That Apply formats. In development: the NGN item types — Matrix/Grid, Bow-Tie, Extended Multiple Response, Drag and Drop, Cloze, and Enhanced Hot Spot. Coming soon: NGN case studies. Anything not yet released is labelled as such in the app.</p></details>
          <details><summary>What are clinical judgment questions?</summary><p>Questions that give you a clinical picture — the client, the timeline, the findings — and ask you to decide, rather than recall a fact. They test whether you can recognize the cues that matter, weigh them, act, and evaluate the result.</p></details>
          <details><summary>Are rationales included?</summary><p>Yes, on every answer choice. You get the reasoning for the correct answer and for each distractor, in plain clinical language, immediately after you submit.</p></details>
          <details><summary>Can I practice by topic?</summary><p>Yes. You can filter a session by nursing system, category, difficulty, available question type, and question count before you start.</p></details>
          <details><summary>Does NextWise track my weak areas?</summary><p>Yes. Accuracy accumulates by category and subcategory, and your weakest areas surface on the dashboard as a specific recommended next quiz.</p></details>
          <details><summary>Is there a free plan?</summary><p>Yes. You can start practicing free, with no credit card. Plan limits and pricing are still being finalized.</p></details>
          <details><summary>How is NextWise different from other NCLEX question banks?</summary><p>Three things: questions are written for clinical judgment rather than recall, every answer choice is explained rather than just marked, and your results decide what you practice next instead of leaving you to plan a study session from a blank screen.</p></details>
          <details><summary>Can I practice under timed conditions?</summary><p>Yes. A timer is configurable per session, so you can simulate exam conditions or work untimed. Sessions save automatically if you need to stop mid-quiz.</p></details>
        </div>
      </div>
    </section>

    <section className="final">
      <div className="ph" style={{ backgroundImage: `url(${finalCtaPhoto})` }}></div>
      <div className="wash"></div>
      <div className="wrap final-in">
        <span className="chip chip-glass" style={{height: '28px', padding: '0 14px'}}>Start today</span>
        <h2>Your NCLEX preparation should get smarter every time you practice.</h2>
        <p>Practice clinical judgment. Understand your mistakes. Find your weak areas. Know what to practice next.</p>
        <div className="final-cta">
          <Link className="btn btn-lg" style={{background: '#fff', color: 'var(--primary)'}} to={ROUTES.register}>Start Practicing Free</Link>
          <Link className="btn btn-glass btn-lg" to={ROUTES.login}>Log In</Link>
        </div>
      </div>
    </section>
    </>
  );
}
