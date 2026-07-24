"use client";
import { useState } from "react";
import { Button, Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger, Input, Label, Textarea } from "@identitycore/ui";
import { updateTemplate, type TemplateRecord } from "@/features/templates/live-data";
export function EditTemplateDialog({ template, onComplete }: { template: TemplateRecord; onComplete?: () => void }) {
 const [name,setName]=useState(template.name); const [description,setDescription]=useState(template.description); const [error,setError]=useState<string|null>(null); const [submitting,setSubmitting]=useState(false);
 async function submit(){setSubmitting(true);setError(null);try{await updateTemplate(template.id,{name});onComplete?.();}catch(cause){setError(cause instanceof Error?cause.message:"Unable to update template.");}finally{setSubmitting(false);}}
 return <Dialog><DialogTrigger asChild><Button variant="outline">Edit draft</Button></DialogTrigger><DialogContent><DialogHeader><DialogTitle>Edit {template.name}</DialogTitle><DialogDescription>Update the draft name and description.</DialogDescription></DialogHeader><div className="space-y-3"><div><Label htmlFor="edit-template-name">Name</Label><Input id="edit-template-name" value={name} onChange={e=>setName(e.target.value)}/></div><div><Label htmlFor="edit-template-description">Description</Label><Textarea id="edit-template-description" value={description} onChange={e=>setDescription(e.target.value)}/></div></div>{error&&<p role="alert" className="text-sm text-red-700">{error}</p>}<DialogFooter><Button onClick={submit} disabled={submitting||!name.trim()}>{submitting?"Saving…":"Save draft"}</Button></DialogFooter></DialogContent></Dialog>;
}
