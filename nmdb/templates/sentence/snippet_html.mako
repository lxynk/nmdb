<%inherit file="../snippet.mako"/>
<%namespace name="util" file="../util.mako"/>

${h.rendered_sentence(ctx)}

<dl>
##% if ctx.source:
##<dt>${_('Type')}:</dt>
##<dd>${ctx.type}</dd>
##% endif
% if ctx.references or ctx.source:
<dt>${_('Source')}:</dt>
% if ctx.source:
<dd>${ctx.source}</dd>
% endif
% if ctx.references:
<dd>${h.linked_references(request, ctx)|n}</dd>
% endif
% endif
% if ctx.comment:
<dt>${_('Comment')}:</dt>
<dd>${ctx.markup_comment or ctx.comment|n}</dd>
% endif
</dl>
