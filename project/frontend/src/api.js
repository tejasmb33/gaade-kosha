import axios from 'axios';
// Public backend origin only. API keys and moderation credentials never belong here.
const origin=(import.meta.env.VITE_BACKEND_ORIGIN||'').replace(/\/$/,'');
export default axios.create({baseURL:origin+'/api'});
