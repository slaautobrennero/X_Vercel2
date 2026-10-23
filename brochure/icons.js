const React = require('react');
const { renderToStaticMarkup } = require('react-dom/server');
const L = require('lucide-react');
const names = ['FolderCheck','TrendingDown','Building2','Globe','UserPlus','MailCheck','KeyRound','LogIn','MapPin','Paperclip','Send','Wallet','FileText','History','Bell','ShieldCheck','Lock','EyeOff','Timer','DatabaseBackup','Scale','HelpCircle','Smartphone','CheckCircle2','Route','Megaphone'];
const out = {};
for (const n of names) out[n] = renderToStaticMarkup(React.createElement(L[n], { size: 22, strokeWidth: 1.8 }));
process.stdout.write(JSON.stringify(out));
