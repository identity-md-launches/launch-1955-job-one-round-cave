// One-time preservation export: keep only imagegen's new pigment silhouette.
'use strict';
const fs=require('node:fs'),zlib=require('node:zlib'),crypto=require('node:crypto');
const {decode,thumbnail}=require('../gathering/thumbnail.js');
const hash=b=>crypto.createHash('sha256').update(b).digest('hex');
const before=fs.readFileSync('artifacts/line-4/wall-v20.png');
const candidateBytes=fs.readFileSync('artifacts/line-4/wall-v21.png');
if(hash(before)!=='eaa5b1e9cdf1c45b8a7344565ec005291327baa5549cf54d51801cf3836fec4a')throw Error('wrong ancestor');
const old=decode(before),candidate=decode(candidateBytes);
if(old.width!==1254||old.height!==1254||candidate.width!==1254||candidate.height!==1254)throw Error('wrong dimensions');
const pixels=Buffer.from(old.pixels),left=1028,top=1050,right=1118,bottom=1140;
function segment(x,y,ax,ay,bx,by){
 const u=Math.max(0,Math.min(1,((x-ax)*(bx-ax)+(y-ay)*(by-ay))/((bx-ax)**2+(by-ay)**2)));
 return Math.hypot(x-ax-u*(bx-ax),y-ay-u*(by-ay));
}
function motif(x,y){
 return Math.hypot(x-1070,y-1087)<13 ||
 [[1039,1058,1047,1095],[1047,1095,1066,1124],[1066,1124,1093,1090],[1093,1090,1110,1058]].some(s=>segment(x,y,...s)<6);
}
let changed=0;
for(let y=top;y<=bottom;y++)for(let x=left;x<=right;x++){
 if(!motif(x,y))continue;
 const p=(y*candidate.width+x)*candidate.channels;
 const [r,g,b]=candidate.pixels.subarray(p,p+3);
 const red=r>g*1.55&&r>95&&g<100&&b<80;
 const black=r<105&&g<90&&b<75;
 if(!red&&!black)continue;
 const a=Math.min(.88,Math.max(0,(red?140-g:130-r)/100));
 if(a<.2)continue;
 const pigment=red?[148,60,27]:[42,30,21],dest=(y*old.width+x)*3;
 for(let c=0;c<3;c++)pixels[dest+c]=Math.round(pixels[dest+c]*(1-a)+pigment[c]*a);
 if(!pixels.subarray(dest,dest+3).equals(old.pixels.subarray(dest,dest+3)))changed++;
}
if(changed<300)throw Error('insufficient pigment');
function crc32(b){let c=0xffffffff;for(const v of b){c^=v;for(let i=0;i<8;i++)c=(c>>>1)^((c&1)?0xedb88320:0);}return(c^0xffffffff)>>>0;}
function chunk(n,b){const k=Buffer.from(n),s=Buffer.alloc(4),c=Buffer.alloc(4);s.writeUInt32BE(b.length);c.writeUInt32BE(crc32(Buffer.concat([k,b])));return Buffer.concat([s,k,b,c]);}
const header=Buffer.alloc(13);header.writeUInt32BE(old.width);header.writeUInt32BE(old.height,4);header[8]=8;header[9]=2;
const stride=old.width*3,scan=Buffer.alloc(old.height*(stride+1));
for(let y=0;y<old.height;y++)pixels.copy(scan,y*(stride+1)+1,y*stride,(y+1)*stride);
const png=Buffer.concat([Buffer.from('89504e470d0a1a0a','hex'),chunk('IHDR',header),chunk('IDAT',zlib.deflateSync(scan,{level:9})),chunk('IEND',Buffer.alloc(0))]);
const jpg=thumbnail(png,512,75);if(jpg.length>100000)throw Error('preview too large');
let outside=0;
for(let y=0;y<old.height;y++)for(let x=0;x<old.width;x++){
 if(x>=left&&x<=right&&y>=top&&y<=bottom)continue;
 const p=(y*old.width+x)*3;if(!pixels.subarray(p,p+3).equals(old.pixels.subarray(p,p+3)))outside++;
}
if(outside)throw Error('ancestor pixels changed');
for(const name of ['wall-v21.png','wall.png'])fs.writeFileSync('artifacts/line-4/'+name,png);
fs.writeFileSync('dist/line-4/41.jpg',jpg);
const checks={ancestor_sha256:hash(before),generated_candidate_sha256:hash(candidateBytes),
 method:'Built-in imagegen edit; only the new forked twig and seed pigment transferred in place on bare rock. Generated scene repaint discarded; candidate consumed in place.',
 png:{paths:['artifacts/line-4/wall-v21.png','artifacts/line-4/wall.png'],format:'PNG',mode:'RGB',dimensions:[1254,1254],bytes:png.length,sha256:hash(png)},
 jpeg:{path:'dist/line-4/41.jpg',format:'JPEG',dimensions:[512,512],bytes:jpg.length,sha256:hash(jpg)},
 preservation:{rectangle:[left,top,right,bottom],changed_pixels:changed,outside_rectangle_changed_pixels:outside},
 visual_review_completed:false,unmet_visual_requirements:[]};
fs.writeFileSync('line-4/image-checks41.json',JSON.stringify(checks,null,2)+'\n');console.log(JSON.stringify(checks,null,2));
