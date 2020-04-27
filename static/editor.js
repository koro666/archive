$(document).ready(function()
{
	$('#copy').click(function(e)
	{
		let links = $('input[name=ids]:checked').next('a');
		if (links.length > 0)
		{
			let buffer = $('#buffer');
			let parent = buffer.parent();

			buffer.val('');
			links.each(function(_, a)
			{
				buffer.val(function(_, text)
				{
					return text + a.href + '\n';
				});
			});

			parent.removeClass('hidden');
			buffer.select();
			let copied = document.execCommand('copy');
			parent.addClass('hidden');

			if (copied)
				alert('Links were copied to the clipboard.');
		}

		e.preventDefault();
	});
});
