import units from '../../public/data/tax-units.json';
import pilots from './governments.json';
const aliases={"227-104-03":"austin","141-000-00":"lampasas-county","050-101-03":"copperas-cove","050-902-02":"gatesville-isd","050-102-03":"gatesville","014-000-00":"bell-county","050-000-00":"coryell-county","050-910-02":"copperas-cove-isd"} as Record<string,string>;
export const profiles=units.map(u=>{const pilot=pilots.find(p=>p.id===aliases[u.id]);return {...(pilot??{count:null,principal:null,interest:null,repayment:null,type:'UNKNOWN'}),id:pilot?.id??u.id,name:pilot?.name??(u.id.endsWith('-000-00')?u.name+' County':u.name),taxId:u.id,rates:u.rates};});
