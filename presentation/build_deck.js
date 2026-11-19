const pptxgen = require('pptxgenjs');
const pptx = new pptxgen();
pptx.layout = 'LAYOUT_WIDE';
pptx.author = 'PapilAlert Project Team';
pptx.subject = 'Future Health Digital Innovation Challenge — research prototype';
pptx.title = 'PapilAlert: Optic-Disc Workflow Research Prototype';
pptx.company = 'PapilAlert';
pptx.lang = 'en-US';
pptx.theme = {
  headFontFace: 'Aptos Display',
  bodyFontFace: 'Aptos',
  lang: 'en-US'
};
pptx.defineSlideMaster({
  title: 'LIGHT',
  background: { color: 'F4F7FA' },
  objects: [
    { line: { x: 0.55, y: 7.08, w: 12.23, h: 0, line: { color: 'DEE5EC', width: 0.7 } } },
    { text: { text: 'PAPILALERT  /  RESEARCH PROTOTYPE', options: { x: 0.58, y: 7.13, w: 5.5, h: 0.16, fontFace: 'Aptos', fontSize: 7.5, color: '8795A5', charSpacing: 1.2, margin: 0 } } },
    { text: { text: 'NOT FOR CLINICAL USE', options: { x: 9.8, y: 7.13, w: 2.4, h: 0.16, fontFace: 'Aptos', fontSize: 7.5, color: 'B27A31', align: 'right', charSpacing: 1, margin: 0 } } }
  ],
  slideNumber: { x: 12.55, y: 7.11, color: '8795A5', fontFace: 'Aptos', fontSize: 8 }
});
const C = { navy:'101C2C', navy2:'1B3046', teal:'18A696', tealDark:'0D756D', pale:'DFF4F0', blue:'467DA8', paleBlue:'E7F0F8', amber:'D89A35', paleAmber:'FFF2DD', red:'BE5551', paleRed:'FBECEB', ink:'17283B', muted:'667789', light:'F4F7FA', line:'DEE5EC', white:'FFFFFF', gray:'9AA7B5', dark2:'273B50' };
const W=13.333, H=7.5;
function addText(s, text, x,y,w,h, opt={}) {
  s.addText(text, { x,y,w,h, fontFace: opt.fontFace || 'Aptos', fontSize: opt.fontSize || 12,
    color: opt.color || C.ink, bold: !!opt.bold, italic: !!opt.italic, margin: opt.margin !== undefined ? opt.margin : 0,
    breakLine: false, valign: opt.valign || 'mid', align: opt.align || 'left',
    fit: 'shrink', paraSpaceAfterPt: opt.paraSpaceAfterPt || 0,
    charSpacing: opt.charSpacing || 0, bullet: opt.bullet, transparency: opt.transparency || 0,
    isTextBox: true, ...opt.extra });
}
function rect(s,x,y,w,h,fill,opts={}) {
  s.addShape(pptx.ShapeType.roundRect,{x,y,w,h,rectRadius:opts.radius||0.12,fill:{color:fill,transparency:opts.transparency||0},line:{color:opts.line||fill,transparency:opts.lineTransparency!==undefined?opts.lineTransparency:100,width:opts.lineWidth||0.8},radius:opts.radius||0.12});
}
function line(s,x1,y1,x2,y2,color=C.line,width=1,dash='solid') { s.addShape(pptx.ShapeType.line,{x:x1,y:y1,w:x2-x1,h:y2-y1,line:{color,width,dashType:dash,beginArrowType:'none',endArrowType:'none'}}); }
function circle(s,x,y,d,fill,lineColor=fill,lineWidth=0.8,trans=0){s.addShape(pptx.ShapeType.ellipse,{x,y,w:d,h:d,fill:{color:fill,transparency:trans},line:{color:lineColor,width:lineWidth,transparency:lineColor===fill?100:0}});}
function header(s,kicker,title,subtitle=''){
  addText(s,kicker.toUpperCase(),0.62,0.42,8,0.22,{fontSize:9,bold:true,color:C.teal,charSpacing:2});
  addText(s,title,0.62,0.76,12,0.52,{fontSize:26,bold:true,color:C.navy,fontFace:'Aptos Display'});
  if(subtitle) addText(s,subtitle,0.64,1.36,11.9,0.34,{fontSize:11,color:C.muted});
}
function card(s,x,y,w,h,title,body,accent=C.teal,number=null){
  rect(s,x,y,w,h,C.white,{line:C.line,lineTransparency:0,lineWidth:0.7});
  rect(s,x,y,0.07,h,accent,{radius:0.04});
  if(number) addText(s,number,x+0.2,y+0.16,0.4,0.26,{fontSize:10,bold:true,color:accent});
  addText(s,title,x+0.22,y+0.18,w-0.42,0.32,{fontSize:14,bold:true,color:C.navy});
  addText(s,body,x+0.22,y+0.60,w-0.42,h-0.72,{fontSize:10.5,color:C.muted,valign:'top',extra:{breakLine:false}});
}
function footnote(s,txt){addText(s,txt,0.66,6.76,11.9,0.18,{fontSize:7.4,color:'8997A5'});}

// 1 — cover
{
  const s=pptx.addSlide(); s.background={color:C.navy};
  // abstract optic-disc-inspired rings, deliberately illustrative, not a clinical image
  circle(s,8.35,0.55,4.2,'17324A','2C566C',1.2,8);
  circle(s,8.92,1.12,3.05,'234B61','458A8A',1.3,12);
  circle(s,9.52,1.72,1.85,'286A73','54B4A4',1.4,6);
  circle(s,10.12,2.32,0.66,'D9B77D','F0D8A9',1.0,0);
  // radial strokes
  for(let i=0;i<18;i++){
    const a=i*Math.PI/9; const x1=10.45+Math.cos(a)*0.50, y1=2.65+Math.sin(a)*0.50;
    const x2=10.45+Math.cos(a)*1.30, y2=2.65+Math.sin(a)*1.30;
    line(s,x1,y1,x2,y2,'58A9A0',0.8);
  }
  addText(s,'FUTURE HEALTH  /  DIGITAL INNOVATION CHALLENGE',0.72,0.75,7.0,0.24,{fontSize:9,bold:true,color:'74D6CA',charSpacing:1.6});
  addText(s,'PapilAlert',0.72,1.47,7.0,0.75,{fontSize:42,bold:true,color:C.white,fontFace:'Aptos Display'});
  addText(s,'A safer first step\nfor optic-disc image workflows',0.75,2.35,6.7,1.08,{fontSize:22,color:'E6F0F5',fontFace:'Aptos Display',valign:'top'});
  addText(s,'Research prototype · image quality · uncertainty · clinician review',0.76,3.75,6.6,0.35,{fontSize:12,color:'9FB6C9'});
  rect(s,0.75,5.18,5.4,0.72,'203B51',{line:'34576B',lineTransparency:0});
  addText(s,'IMPORTANT',0.98,5.35,1.1,0.18,{fontSize:8.5,bold:true,color:'F0BD67',charSpacing:1.4});
  addText(s,'Not a medical device. No clinical model is bundled.',2.0,5.30,3.9,0.28,{fontSize:10,color:C.white,bold:true});
  addText(s,'PapilAlert  |  Prototype v0.1  |  17 November 2026',0.76,6.78,7.2,0.2,{fontSize:8,color:'8FA5B8'});
  s.addNotes('Open with the clinical workflow problem. Say explicitly that this is a research demonstrator, not a diagnostic tool. A normal phone camera cannot photograph the retina; a fundus camera or optical attachment is required.');
}

// 2 problem
{
  const s=pptx.addSlide('LIGHT'); header(s,'01 / Clinical need','The signal matters — but the image is only the beginning','Papilledema is optic-disc swelling associated with raised intracranial pressure; look-alikes and other optic neuropathies complicate assessment.');
  card(s,0.68,2.0,3.85,2.05,'A clinically important finding','Optic-disc swelling can be a clue to raised intracranial pressure and needs appropriate clinical evaluation.',C.red,'01');
  card(s,4.74,2.0,3.85,2.05,'A difficult visual differential','Pseudopapilledema and other optic-disc abnormalities can resemble swelling. A fundus image alone is not the whole work-up.',C.amber,'02');
  card(s,8.80,2.0,3.85,2.05,'An access and workflow gap','Non-specialists may not confidently perform ophthalmoscopy. Images must be usable, interpreted cautiously and connected to care.',C.teal,'03');
  rect(s,0.68,4.45,11.97,1.34,C.navy,{line:C.navy});
  addText(s,'THE PRODUCT QUESTION',0.98,4.73,2.0,0.2,{fontSize:8,bold:true,color:'72D5C7',charSpacing:1.4});
  addText(s,'How might we make an optic-disc image workflow more reliable before a clinician acts on it?',0.98,5.05,10.9,0.42,{fontSize:20,bold:true,color:C.white,fontFace:'Aptos Display'});
  footnote(s,'Clinical framing: BONSAI study, NEJM 2020. See references slide.');
  s.addNotes('Do not say that the app diagnoses raised intracranial pressure. Papilledema is one cause of optic-disc swelling and a fundus photograph cannot measure intracranial pressure.');
}

// 3 Prior art
{
  const s=pptx.addSlide('LIGHT'); header(s,'02 / Prior art','Automated optic-disc detection is already established research','We are not claiming to have invented papilledema detection. The best-known example is the BONSAI deep-learning system.');
  rect(s,0.68,1.95,7.2,3.9,C.navy,{line:C.navy});
  addText(s,'BONSAI  ·  NEJM 2020',1.0,2.24,4,0.25,{fontSize:10,bold:true,color:'71D4C7',charSpacing:1.2});
  addText(s,'15,846',1.0,2.75,3.2,0.74,{fontSize:42,bold:true,color:C.white,fontFace:'Aptos Display'});
  addText(s,'fundus photographs',1.05,3.52,3.3,0.25,{fontSize:13,color:'C5D5E1'});
  line(s,4.35,2.70,4.35,4.8,'476075',1);
  addText(s,'14,341',4.72,2.85,2.2,0.52,{fontSize:27,bold:true,color:C.white});
  addText(s,'training + validation',4.75,3.37,2.4,0.22,{fontSize:10,color:'C5D5E1'});
  addText(s,'1,505',4.72,4.05,2.2,0.48,{fontSize:24,bold:true,color:'76D6CA'});
  addText(s,'external test images',4.75,4.52,2.4,0.22,{fontSize:10,color:'C5D5E1'});
  addText(s,'19 centres · 11 countries',1.02,5.25,5.8,0.24,{fontSize:10,color:'C5D5E1'});
  card(s,8.18,1.95,4.45,1.68,'What this means','The disease-classification task is not new. A credible project must differentiate through workflow, data quality, uncertainty and validation.',C.teal);
  card(s,8.18,3.82,4.45,2.03,'Our positioning','A quality-gated, auditable research workflow for supervised assessment — not a claim to outperform BONSAI or specialists.',C.amber);
  footnote(s,'Source: Miller et al., “Artificial Intelligence to Detect Papilledema from Ocular Fundus Photographs,” NEJM 2020;382:1687–1695.');
  s.addNotes('Judges may know BONSAI. Acknowledge it first. It prevents an overclaim. Explain that our proposed value is workflow-quality and uncertainty handling, subject to validation—not novel disease detection.');
}

// 4 LLM comparison
{
  const s=pptx.addSlide('LIGHT'); header(s,'03 / General-purpose AI','A vision-language model is not automatically a validated screen','A 2025 benchmark found substantial variability across general VLMs and prompts for optic-disc swelling.');
  rect(s,0.68,2.0,5.15,3.85,C.white,{line:C.line,lineTransparency:0});
  addText(s,'27.5–70.5%',1.0,2.48,4.4,0.68,{fontSize:38,bold:true,color:C.navy,fontFace:'Aptos Display'});
  addText(s,'accuracy range across 25 model–prompt pairs',1.04,3.15,4.25,0.32,{fontSize:12,color:C.muted});
  line(s,1.05,3.88,5.4,3.88,C.line,5);
  line(s,2.25,3.88,4.1,3.88,C.teal,5);
  circle(s,2.17,3.78,0.20,C.teal);
  circle(s,4.00,3.78,0.20,C.teal);
  addText(s,'27.5%',1.93,4.18,1.0,0.25,{fontSize:10,bold:true,color:C.teal});
  addText(s,'70.5%',3.83,4.18,1.0,0.25,{fontSize:10,bold:true,color:C.teal});
  addText(s,'5 VLMs × 5 prompts · median accuracy 58.8%',1.04,4.85,4.5,0.35,{fontSize:11,bold:true,color:C.ink});
  addText(s,'The study used models updated around April 2025. It is not a benchmark of every current consumer AI model.',1.04,5.27,4.4,0.42,{fontSize:9,color:C.muted,valign:'top'});
  card(s,6.18,2.0,6.45,1.58,'What an LLM can do','Describe an image, explain conditions, summarize context and help draft a report.',C.blue);
  card(s,6.18,3.78,6.45,2.07,'What a validated imaging workflow must add','Controlled image input, quality rejection, task-specific evaluation, calibrated uncertainty, external validation, auditability and a human decision pathway.',C.teal);
  footnote(s,'Source: Li, Nguyen & Moss, Frontiers in Digital Health, 25 Aug 2025, DOI 10.3389/fdgth.2025.1660887.');
  s.addNotes('Be precise: the paper tested five non-specialty-trained VLMs and five prompts. Accuracy ranged from 27.5 to 70.5 percent, median 58.8. This shows variability in that benchmark; it does not prove all present-day ChatGPT systems fail.');
}

// 5 workflow
{
  const s=pptx.addSlide('LIGHT'); header(s,'04 / Product workflow','From image capture to a reviewable signal','The product is a controlled workflow with an explicit stop/abstain path.');
  const steps=[
    ['01','CAPTURE','Fundus camera or validated phone adapter',C.blue],
    ['02','QUALITY GATE','Resolution · blur · exposure · clipping',C.teal],
    ['03','TASK MODEL','Class scores from a specialist image model',C.amber],
    ['04','UNCERTAINTY','Abstain when evidence is insufficient',C.red],
    ['05','HUMAN REVIEW','Qualified eye-care professional decides',C.navy2]
  ];
  const x0=0.64, y=2.5, gap=0.22, cw=2.3;
  steps.forEach((st,i)=>{
    const x=x0+i*(cw+gap);
    rect(s,x,y,cw,2.08,C.white,{line:C.line,lineTransparency:0});
    circle(s,x+0.18,y+0.18,0.38,st[3]);
    addText(s,st[0],x+0.18,y+0.27,0.38,0.12,{fontSize:8,bold:true,color:C.white,align:'center'});
    addText(s,st[1],x+0.18,y+0.78,cw-0.32,0.26,{fontSize:12,bold:true,color:C.navy});
    addText(s,st[2],x+0.18,y+1.16,cw-0.34,0.63,{fontSize:10,color:C.muted,valign:'top'});
    if(i<steps.length-1) addText(s,'›',x+cw+0.03,y+0.86,0.15,0.35,{fontSize:24,bold:true,color:C.teal,align:'center'});
  });
  rect(s,0.68,5.0,11.97,0.92,C.paleAmber,{line:'F0DCB5',lineTransparency:0});
  addText(s,'SAFETY RULE',0.98,5.23,1.3,0.18,{fontSize:8,bold:true,color:'9A671D',charSpacing:1.3});
  addText(s,'No automatic diagnosis. No “all clear” message. Uncertain or poor-quality images go to human review.',2.32,5.16,9.8,0.34,{fontSize:13,bold:true,color:'61471F'});
  footnote(s,'A fundus camera or compatible optical attachment is required. Ordinary selfie/rear-camera photos are not fundus images.');
  s.addNotes('Walk through the workflow. Emphasize that current code implements the upload, engineering QC checks and optional model loader. The task model is a future/optional checkpoint, not currently bundled.');
}

// 6 prototype today
{
  const s=pptx.addSlide('LIGHT'); header(s,'05 / What is built','A working software shell — with no fake medical prediction','The current prototype is functional for upload and image checks. Classifier inference activates only when a compatible trained checkpoint is installed.');
  const rows=[
    ['Image upload + preview','BUILT',C.teal],
    ['Resolution / exposure / clipping checks','BUILT',C.teal],
    ['Blur proxy using Laplacian variance','BUILT',C.teal],
    ['Optional MobileNetV3 checkpoint loader','BUILT',C.teal],
    ['Trained papilledema-specific weights','NOT INCLUDED',C.red],
    ['Clinical triage / patient referral','NOT IMPLEMENTED',C.red],
  ];
  rect(s,0.72,1.95,7.2,3.95,C.white,{line:C.line,lineTransparency:0});
  rows.forEach((r,i)=>{
    const yy=2.20+i*0.56;
    addText(s,r[0],1.0,yy,4.9,0.24,{fontSize:11,bold:i===0,color:C.ink});
    rect(s,6.05,yy-0.02,1.48,0.31,r[2]===C.teal?C.pale:C.paleRed,{line:r[2],lineTransparency:100});
    addText(s,r[1],6.12,yy+0.045,1.34,0.14,{fontSize:7.5,bold:true,color:r[2],align:'center',charSpacing:.6});
    if(i<rows.length-1) line(s,1.0,yy+0.40,7.5,yy+0.40,'EDF1F4',0.6);
  });
  card(s,8.28,1.95,4.34,1.62,'Why no weights?','The commonly cited dataset has a mixed abnormal class and unresolved access/provenance concerns. Shipping a model would imply evidence we do not have.',C.amber);
  card(s,8.28,3.78,4.34,2.12,'What this demonstrates','A live upload workflow, transparent technical checks, a reusable trainer/evaluator and a responsible boundary between research code and clinical claims.',C.teal);
  footnote(s,'The app reports basic engineering checks only; their thresholds are not clinical image-quality standards.');
  s.addNotes('Show the actual app. Do not hide the “no trained checkpoint” message. Judges tend to trust teams more when they distinguish what is built from what remains to be validated.');
}

// 7 architecture
{
  const s=pptx.addSlide('LIGHT'); header(s,'06 / Technical architecture','A lightweight, inspectable pipeline','The implementation uses a small local model architecture with a reproducible data and evaluation path.');
  const bx=0.75, by=2.0;
  const boxes=[
    ['BROWSER','Responsive HTML / CSS / JS',C.blue],
    ['FASTAPI','Upload validation + image decode',C.teal],
    ['IMAGE QC','Dimensions · brightness · blur proxy',C.amber],
    ['MOBILENETV3','Optional local checkpoint',C.red],
    ['ABSTAIN','Low score / low margin',C.navy2]
  ];
  boxes.forEach((b,i)=>{
    const x=bx+i*2.5;
    rect(s,x,2.45,2.12,1.28,C.white,{line:C.line,lineTransparency:0});
    rect(s,x,2.45,2.12,0.09,b[2],{line:b[2]});
    addText(s,b[0],x+0.15,2.73,1.82,0.22,{fontSize:10,bold:true,color:C.navy,align:'center'});
    addText(s,b[1],x+0.15,3.08,1.82,0.42,{fontSize:9,color:C.muted,align:'center'});
    if(i<boxes.length-1) addText(s,'→',x+2.17,2.87,0.28,0.22,{fontSize:17,bold:true,color:C.teal,align:'center'});
  });
  rect(s,0.75,4.35,5.68,1.48,C.navy,{line:C.navy});
  addText(s,'TRAINING',1.02,4.62,1.2,0.18,{fontSize:9,bold:true,color:'75D6C9',charSpacing:1.3});
  addText(s,'Manifest → patient-group split → MobileNetV3-Small → best checkpoint',1.02,4.96,5.0,0.38,{fontSize:12,bold:true,color:C.white});
  rect(s,6.68,4.35,5.68,1.48,C.navy,{line:C.navy});
  addText(s,'EVALUATION',6.95,4.62,1.5,0.18,{fontSize:9,bold:true,color:'75D6C9',charSpacing:1.3});
  addText(s,'Held-out confusion matrix · class metrics · split audit',6.95,4.96,5.0,0.38,{fontSize:12,bold:true,color:C.white});
  footnote(s,'Stack: Python · FastAPI · PyTorch · torchvision · scikit-learn · Pillow · OpenCV.');
  s.addNotes('Explain that MobileNetV3-Small is a compact baseline, not the state-of-the-art architecture. The trainer uses class-weighted loss, mild augmentation and early stopping. The default split is patient-grouped; image-only split requires explicit override.');
}

// 8 dataset audit
{
  const s=pptx.addSlide('LIGHT'); header(s,'07 / Data honesty','The popular 1,369-image dataset is not a clean papilledema dataset','The original paper describes a mixed optic-neuropathy category — not 295 confirmed papilledema cases.');
  rect(s,0.68,1.95,5.75,3.92,C.white,{line:C.line,lineTransparency:0});
  addText(s,'295 mixed optic-neuropathy images',1.02,2.24,4.9,0.31,{fontSize:15,bold:true,color:C.navy});
  const parts=[['Ischemic optic neuropathy',177,C.blue],['Optic neuritis',48,C.teal],['Diabetic optic neuropathy',17,C.amber],['Papilledema',22,C.red],['Retinal disorders',31,C.navy2]];
  const total=295; let yy=2.88;
  parts.forEach(p=>{
    addText(s,p[0],1.03,yy,2.65,0.18,{fontSize:9.5,color:C.muted});
    rect(s,3.55,yy+0.01,1.95,0.14,'EDF1F4',{line:'EDF1F4'});
    rect(s,3.55,yy+0.01,1.95*p[1]/total,0.14,p[2],{line:p[2]});
    addText(s,String(p[1]),5.62,yy-0.01,0.38,0.18,{fontSize:9.5,bold:true,color:C.ink,align:'right'});
    yy+=0.49;
  });
  rect(s,6.78,1.95,5.85,1.62,C.paleRed,{line:'EFCFCB',lineTransparency:0});
  addText(s,'02 NOV 2026  ·  EDITORIAL EXPRESSION OF CONCERN',7.05,2.20,5.15,0.2,{fontSize:8,bold:true,color:C.red,charSpacing:.8});
  addText(s,'Publisher: authors had not responded to requests for dataset access.',7.05,2.57,5.1,0.54,{fontSize:14,bold:true,color:'6D3232',valign:'top'});
  rect(s,6.78,3.82,5.85,2.05,C.navy,{line:C.navy});
  addText(s,'OUR DECISION',7.05,4.11,2.0,0.2,{fontSize:9,bold:true,color:'74D6CA',charSpacing:1.2});
  addText(s,'No bundled weights. A separate CC BY 4.0 set has 100 images but only 4 papilledema cases — too few for a detector. No papilledema-specific claim from mixed labels.',7.05,4.53,5.1,0.82,{fontSize:13,bold:true,color:C.white,valign:'top'});
  footnote(s,'Sources: Ahn et al., BMC Ophthalmology 2019; Expression of Concern 2 Nov 2026; Akram et al., Data in Brief 2020.');
  s.addNotes('This is a credibility slide. Explain the exact label mixture: 177 ischemic optic neuropathy, 48 optic neuritis, 17 diabetic optic neuropathy, 22 papilledema, 31 retinal disorders. The expression of concern says the authors did not respond to requests for dataset access. It does not itself prove misconduct or invalidate every result, but it raises auditability concerns.');
}

// 9 validation
{
  const s=pptx.addSlide('LIGHT'); header(s,'08 / Validation plan','We evaluate safety and generalization, not just accuracy','A clinically credible model needs patient-independent splits and external testing.');
  card(s,0.68,2.0,3.78,1.88,'Patient-level split','All images, both eyes and repeated visits from one person stay in one partition.',C.teal,'01');
  card(s,4.78,2.0,3.78,1.88,'External-site test','Hold out a different clinic, camera or acquisition setting to test distribution shift.',C.blue,'02');
  card(s,8.88,2.0,3.78,1.88,'Uncertainty + calibration','Measure abstention, calibration and failure cases. Do not call raw softmax a probability.',C.amber,'03');
  rect(s,0.68,4.28,11.98,1.44,C.navy,{line:C.navy});
  const metrics=[['Sensitivity','per class'],['Specificity','per class'],['Macro-F1','balanced view'],['AUPRC / AUROC','where valid'],['Abstention','uncertain rate'],['Subgroups','site / device']];
  metrics.forEach((m,i)=>{
    const x=0.95+i*1.92;
    addText(s,m[0],x,4.67,1.7,0.22,{fontSize:11,bold:true,color:C.white,align:'center'});
    addText(s,m[1],x,5.00,1.7,0.19,{fontSize:8.5,color:'A8BAC8',align:'center'});
  });
  footnote(s,'No performance values are reported because no valid trained checkpoint and independent test cohort are included.');
  s.addNotes('Describe the difference between a random image split and a patient-group split. A site-held-out test is stronger. Metrics must include class-wise sensitivity, false-negative rates for the important target, calibration, abstention, image quality rejection and confidence intervals bootstrapped by patient.');
}

// 10 safeguards
{
  const s=pptx.addSlide('LIGHT'); header(s,'09 / Responsible AI','Safety is a product feature, not a disclaimer','The prototype is deliberately constrained to research demonstration.');
  const safeguards=[
    ['No diagnosis','No disease label is returned without an installed research checkpoint; even then it is not a diagnosis.',C.red],
    ['No “all clear”','The UI never tells a patient they are normal or safe. Poor-quality and uncertain images need human review.',C.amber],
    ['Data minimization','Images are processed in memory; use de-identified, consented images. Production hosting needs a privacy review.',C.blue],
    ['No autonomous triage','No treatment or emergency-disposition recommendation is generated.',C.teal]
  ];
  safeguards.forEach((a,i)=>{
    const x=0.7+(i%2)*6.08, y=2.0+Math.floor(i/2)*1.78;
    card(s,x,y,5.75,1.48,a[0],a[1],a[2]);
  });
  rect(s,0.7,5.75,11.83,0.42,C.paleAmber,{line:'F0DCB5',lineTransparency:0});
  addText(s,'Any future clinical use requires institutional governance, prospective validation and regulatory review.',0.95,5.86,11.2,0.18,{fontSize:10,bold:true,color:'73521F',align:'center'});
  footnote(s,'Do not upload identifiable patient images to a public demo. Localhost is not a complete production security model.');
  s.addNotes('Point out the product has no diagnosis, no automated triage and no patient-facing reassurance. It is a prototype. Any real deployment needs clinical governance and regulatory assessment in the target jurisdiction.');
}

// 11 deployment
{
  const s=pptx.addSlide('LIGHT'); header(s,'10 / Roadmap','From hackathon prototype to responsible pilot','The next milestone is not “more layers”; it is a better dataset and a supervised workflow.');
  const phases=[
    ['NOW','Prototype','Upload · technical QC · training pipeline · evaluator',C.teal],
    ['NEXT','Data partnership','Clinician adjudication · licenses · patient-level IDs · reference standards',C.blue],
    ['THEN','Retrospective validation','External site · camera shift · calibration · subgroup analysis',C.amber],
    ['LATER','Silent-mode pilot','Workflow time · ungradable rate · referral completion · safety monitoring',C.red]
  ];
  phases.forEach((p,i)=>{
    const y=2.0+i*0.94;
    circle(s,0.9,y+0.06,0.38,p[3]);
    addText(s,String(i+1),0.9,y+0.15,0.38,0.12,{fontSize:9,bold:true,color:C.white,align:'center'});
    if(i<phases.length-1) line(s,1.09,y+0.44,1.09,y+0.99,'C7D4DD',1.6);
    addText(s,p[0],1.55,y+0.02,1.25,0.18,{fontSize:8,bold:true,color:p[3],charSpacing:1});
    addText(s,p[1],2.8,y-0.01,2.5,0.25,{fontSize:13,bold:true,color:C.navy});
    addText(s,p[2],5.1,y+0.02,6.9,0.27,{fontSize:10,color:C.muted});
  });
  rect(s,0.74,6.05,11.85,0.45,C.navy,{line:C.navy});
  addText(s,'NEED: ophthalmology partner + permitted multi-site dataset + clinical governance',0.98,6.18,11.35,0.17,{fontSize:10,bold:true,color:C.white,align:'center',charSpacing:.2});
  footnote(s,'Roadmap is proposed work, not an existing deployment or partnership.');
  s.addNotes('Do not imply that partnerships or pilots already exist. Say that these are the next milestones. The first critical deliverable is access to an auditable, patient-linked dataset with clinical adjudication.');
}

// 12 challenge fit
{
  const s=pptx.addSlide('LIGHT'); header(s,'11 / Competition fit','Potential Population Health fit — verify the exact statement','PapilAlert could be framed as earlier identification and referral support in an eye-care pathway, but the fit is not confirmed from the public page.');
  rect(s,0.72,2.0,5.6,3.82,C.navy,{line:C.navy});
  addText(s,'PUBLIC EVENT PAGE',1.02,2.30,3.0,0.18,{fontSize:8,bold:true,color:'71D4C7',charSpacing:1.4});
  addText(s,'10',1.00,2.78,1.2,0.8,{fontSize:50,bold:true,color:C.white,fontFace:'Aptos Display'});
  addText(s,'challenge statements',2.12,3.18,2.95,0.25,{fontSize:13,color:'D7E4EC'});
  addText(s,'across fertility, population health and wellbeing',1.02,4.05,4.65,0.5,{fontSize:16,bold:true,color:C.white,valign:'top'});
  addText(s,'Working prototype + technical documentation due 20 Nov 2026',1.02,5.18,4.8,0.24,{fontSize:10,color:'AFC2D0'});
  rect(s,6.72,2.0,5.9,1.62,C.paleAmber,{line:'F0DCB5',lineTransparency:0});
  addText(s,'ALIGNMENT RISK',7.02,2.28,2.0,0.18,{fontSize:8,bold:true,color:'9A671D',charSpacing:1.3});
  addText(s,'The fully rendered public brief is Male Reproductive Health — not a direct match.',7.02,2.66,5.1,0.54,{fontSize:14,bold:true,color:'61471F',valign:'top'});
  rect(s,6.72,3.88,5.9,1.94,C.pale,{line:'CBE8E2',lineTransparency:0});
  addText(s,'BEFORE SUBMISSION',7.02,4.16,2.4,0.18,{fontSize:8,bold:true,color:C.tealDark,charSpacing:1.3});
  addText(s,'Confirm that the selected Population Health or Wellbeing statement explicitly includes ophthalmic early-identification and referral workflows.',7.02,4.55,5.1,0.75,{fontSize:13,bold:true,color:'185D56',valign:'top'});
  footnote(s,'Official event page: hack2skill.com/event/futurehealthchallenge/ · registration closed 10 Nov; working prototype due 20 Nov.');
  s.addNotes('This slide is intentionally candid. Do not claim this project has confirmed challenge fit. The event page lists 10 statements, but the public rendered page only fully exposes the male reproductive health brief. Check the participant portal or contact the organizer before choosing PapilAlert for a strict statement-based competition.');
}

// 13 close + sources
{
  const s=pptx.addSlide(); s.background={color:C.navy};
  addText(s,'PAPILALERT',0.72,0.55,5.0,0.28,{fontSize:10,bold:true,color:'72D5C7',charSpacing:2});
  addText(s,'A workflow worth validating.\nNot a diagnosis to trust blindly.',0.72,1.18,8.4,1.25,{fontSize:28,bold:true,color:C.white,fontFace:'Aptos Display',valign:'top'});
  addText(s,'The next step is clinician-governed data, external validation and a supervised pilot.',0.76,2.8,7.8,0.42,{fontSize:14,color:'B7C8D4'});
  rect(s,0.76,4.0,5.45,1.48,'1B344A',{line:'38566C',lineTransparency:0});
  addText(s,'SELECTED SOURCES',1.02,4.26,2.8,0.2,{fontSize:8,bold:true,color:'72D5C7',charSpacing:1.4});
  addText(s,'BONSAI · NEJM 2020\nAhn et al. · BMC Ophthalmology 2019 + 2026 Expression of Concern\nAkram et al. · Data in Brief 2020 (100 images; 4 papilledema)\nLi et al. · Frontiers Digital Health 2025',1.02,4.58,4.85,0.85,{fontSize:8.3,color:'D6E2EA',valign:'top'});
  addText(s,'Research prototype v0.1  |  No clinical model bundled  |  Not for patient care',0.78,6.77,8.8,0.2,{fontSize:8,color:'8FA5B8'});
  s.addNotes('Close with what is real today and what must come next. The next step is not model tuning on questionable images; it is a clinically governed, auditable dataset and independent validation.');
}

pptx.writeFile({ fileName: __dirname + '/PapilAlert_Pitch_Deck.pptx' });
