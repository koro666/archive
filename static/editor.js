$(document).ready(function()
{
	$('#copy').click(function(e)
	{
		let buffer = $('#buffer');
		let parent = buffer.parent();
		buffer.val('');
		$('input[name=ids]:checked').next('a').each(function(i, o) { buffer.val(function(i, text) { return text + o.href + '\n'; }); });
		parent.removeClass('hidden');
		buffer.select();
		document.execCommand('copy');
		parent.addClass('hidden');
		alert('Links were copied to the clipboard.');
		e.preventDefault();
	});
});
