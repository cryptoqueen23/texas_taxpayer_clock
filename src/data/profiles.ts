import units from '../../public/data/tax-units.json';
import pilots from './governments.json';
import aliasData from './profile-aliases.json';
const aliases=aliasData as Record<string,string>;
export const profiles=units.map(u=>{const pilot=pilots.find(p=>p.id===aliases[u.id]);return {...(pilot??{count:null,principal:null,interest:null,repayment:null,type:'UNKNOWN'}),id:pilot?.id??u.id,name:pilot?.name??(u.id.endsWith('-000-00')?u.name+' County':u.name),taxId:u.id,rates:u.rates};});
