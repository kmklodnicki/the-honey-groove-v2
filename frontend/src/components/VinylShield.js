import React from 'react';
const VINYL_IMG = 'https://static.prod-images.emergentagent.com/jobs/bcb688fd-4e52-4359-88b5-27a51977a715/images/a0ef91b80488fa7a1fc8c5fe5b0c56afe8c6b230aede87ec22f9efd8cd7ad7cc.png';

/* Inject keyframes once */
if (typeof document !== 'undefined' && !document.getElementById('vinyl-shield-kf')) {
  const s = document.createElement('style');
  s.id = 'vinyl-shield-kf';
  s.textContent = `
    @keyframes vs-spin { from { transform: rotate(0deg); } to { transform: rotate(360deg); } }
    @keyframes vs-bob { 0%,100% { transform: rotate(-28deg) translateY(0); } 50% { transform: rotate(-28deg) translateY(2px); } }
    @keyframes vs-fadein { from { opacity:0; transform:translateY(16px); } to { opacity:1; transform:translateY(0); } }
  `;
  document.head.appendChild(s);
}

function ShieldUI({ onRetry }) {
  return (
    <div style={{
      position:'fixed',inset:0,zIndex:9999,
      display:'flex',flexDirection:'column',alignItems:'center',justifyContent:'center',
      background:'linear-gradient(160deg,#FFF8E7 0%,#FFEDB5 40%,#F5C542 100%)',
      fontFamily:"'DM Sans','Inter',system-ui,sans-serif",
      padding:24,textAlign:'center',overflow:'hidden',
    }} data-testid="vinyl-shield">

      {/* Turntable area */}
      <div style={{position:'relative',width:220,height:220,marginBottom:8,animation:'vs-fadein .6s ease-out'}}>
        {/* Vinyl record */}
        <img
          src={VINYL_IMG}
          alt="Vinyl maintenance"
          data-testid="vinyl-shield-spinner"
          style={{
            width:220,height:220,borderRadius:'50%',
            animation:'vs-spin 3s linear infinite',
            filter:'drop-shadow(0 8px 24px rgba(0,0,0,0.3))',
          }}
        />
        {/* Tonearm */}
        <div style={{
          position:'absolute',top:-18,right:-30,width:80,height:130,
          transformOrigin:'12px 12px',
          animation:'vs-bob 2s ease-in-out infinite',
        }}>
          {/* Arm pivot */}
          <div style={{
            position:'absolute',top:0,left:0,width:24,height:24,borderRadius:'50%',
            background:'radial-gradient(circle at 40% 40%,#ddd,#888)',
            border:'2px solid #999',boxShadow:'0 2px 6px rgba(0,0,0,.25)',
          }} />
          {/* Arm shaft */}
          <div style={{
            position:'absolute',top:12,left:10,width:4,height:100,
            background:'linear-gradient(90deg,#bbb,#eee,#bbb)',
            borderRadius:2,transformOrigin:'top center',transform:'rotate(28deg)',
            boxShadow:'1px 1px 4px rgba(0,0,0,.15)',
          }} />
          {/* Cartridge / headshell */}
          <div style={{
            position:'absolute',top:104,left:48,width:14,height:20,
            background:'linear-gradient(180deg,#666,#333)',borderRadius:'2px 2px 1px 1px',
            transform:'rotate(28deg)',boxShadow:'0 2px 4px rgba(0,0,0,.2)',
          }}>
            <div style={{
              position:'absolute',bottom:-3,left:5,width:3,height:6,
              background:'#D4A828',borderRadius:'0 0 1px 1px',
            }} />
          </div>
        </div>
      </div>

      {/* Copy */}
      <h1 style={{
        fontSize:24,fontWeight:700,color:'#5C3D10',marginTop:24,marginBottom:6,
        lineHeight:1.3,maxWidth:380,animation:'vs-fadein .6s ease-out .15s both',
      }}>
        Don't skip a beat!
      </h1>
      <p style={{
        fontSize:15,color:'#7A5A20',maxWidth:340,lineHeight:1.65,marginBottom:28,
        animation:'vs-fadein .6s ease-out .3s both',
      }}>
        Our needle hit a little dust. We're auto-cleaning the grooves right now — try refreshing in a moment!
      </p>

      {/* Retry button */}
      <button
        data-testid="vinyl-shield-retry"
        onClick={onRetry}
        style={{
          background:'#D4A828',color:'#fff',border:'none',borderRadius:999,
          padding:'13px 36px',fontSize:15,fontWeight:600,cursor:'pointer',
          boxShadow:'0 4px 16px rgba(200,134,26,0.4)',
          transition:'transform .15s,box-shadow .15s',
          animation:'vs-fadein .6s ease-out .45s both',
        }}
        onMouseEnter={e => { e.currentTarget.style.transform = 'scale(1.05)'; e.currentTarget.style.boxShadow = '0 6px 20px rgba(200,134,26,0.5)'; }}
        onMouseLeave={e => { e.currentTarget.style.transform = 'scale(1)'; e.currentTarget.style.boxShadow = '0 4px 16px rgba(200,134,26,0.4)'; }}
      >
        Try Again
      </button>
    </div>
  );
}

class VinylShield extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false };
  }

  static getDerivedStateFromError() {
    return { hasError: true };
  }

  componentDidCatch(error, info) {
    console.error('[VinylShield] React error caught:', error, info);
  }

  handleRetry = () => {
    try {
      localStorage.removeItem('honeygroove_token');
      localStorage.removeItem('swr-cache');
      document.cookie.split(';').forEach(c => {
        const name = c.split('=')[0].trim();
        if (name.startsWith('honeygroove') || name.startsWith('next-auth')) {
          document.cookie = `${name}=;expires=Thu, 01 Jan 1970 00:00:00 GMT;path=/`;
        }
      });
    } catch (_) {}
    window.location.href = '/login';
  };

  render() {
    if (this.state.hasError) return <ShieldUI onRetry={this.handleRetry} />;
    return this.props.children;
  }
}

export default VinylShield;
