function fig = plotDXFparsedLayout(x, y, options)
arguments
    x
    y
    options.FontSize (1,1) double = 8;
    options.FontName = 'Consolas';
    options.Label = 'PCB Layout';
    options.Color = [0 0 0];
end
fig = figure('Color','w','Units','inches','Position',[3 3 6 4]);
ax = axes(fig,'XColor','none','YColor','none','NextPlot','add', ...
    'XLim',[min(x),max(x)],'YLim',[min(y),max(y)]);
for ii = 1:size(x,1)
    text(ax,x(ii),y(ii),num2str(ii), ...
        'Color',options.Color,'FontSize',options.FontSize, ...
        'FontName',options.FontName,'FontWeight','bold','HorizontalAlignment','center');
end
title(ax,options.Label,'FontName',options.FontName,'Color',options.Color);

end