import units from '../../public/data/tax-units.json';
import debt from '../../public/data/local-debt-2025.json';
import aliasData from './profile-aliases.json';
const aliases=aliasData as Record<string,string>;
const debtById=new Map(debt.records.map(r=>[r.id,r]));
export const profiles=units.map(u=>{
 const d=debtById.get(u.id);
 return {...(d??{count:null,principal:null,interest:null,repayment:null,type:'UNKNOWN'}),id:aliases[u.id]??u.id,name:u.id.endsWith('-000-00')&&!/ County$/i.test(u.name)?u.name+' County':u.name,taxId:u.id,rates:u.rates,debtName:d?.name??null};
});
