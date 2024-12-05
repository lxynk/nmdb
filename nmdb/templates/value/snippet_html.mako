<%namespace name="util" file="../util.mako"/>

% for a in ctx.sentence_assocs:
    <dl>
        <dt>${h.link(request, a.sentence, label='%s %s:' % (_('Sentence'), a.sentence.id))}</dt>
        <dd>${h.rendered_sentence(a.sentence)}</dd>
        % if a.sentence.source or a.sentence.references:
            Source: ${a.sentence.source or h.linked_references(request, a.sentence)|n}
        % endif
        <br>
        % if a.sentence.comment:
            Comment: ${a.sentence.comment}
        % endif
    </dl>
% endfor
