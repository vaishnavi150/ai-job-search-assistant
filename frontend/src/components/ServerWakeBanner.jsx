import { useEffect, useState } from 'react';
import { onApiEvent } from '../api';

// The free hosting tier sleeps after inactivity; the first request can take
// ~30-60s. Tell the user instead of leaving them staring at a spinner.
export default function ServerWakeBanner() {
  const [slow, setSlow] = useState(false);

  useEffect(() => {
    const offSlow = onApiEvent('api:slow', () => setSlow(true));
    const offSettled = onApiEvent('api:settled', () => setSlow(false));
    return () => {
      offSlow();
      offSettled();
    };
  }, []);

  if (!slow) return null;
  return (
    <div className="wake-banner" role="status">
      <span className="spinner spinner-inline" aria-hidden="true" />
      Still working… AI responses can take a little while, and if the app was idle the server may need up to a minute to wake up.
    </div>
  );
}
