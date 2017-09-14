function initQChannel() {
    return new Promise((resolve, reject) => {
        var channel = new QWebChannel(qt.webChannelTransport, (channel) => {
            if(channel) {
                resolve(channel);
            } else {
                reject(channel);
            }
        });
    });
}

function checkChannelInit() {
    return window.handler !== undefined;
}

function checkSaxonInit() {
    return SaxonJS !== undefined;
}

function addPageBreaks(source) {
    SaxonJS.transform({
       stylesheetLocation: window.stylesheets[2],
       sourceLocation: source,
    }, (result) => console.log(result));
}

function generateHeader(source) {
    SaxonJS.transform({
        stylesheetLocation: window.stylesheets[1],
        sourceLocation: source,
    }, (result) => addPageBreaks(docFragmentToDataURL(result));
}

function docFragmentToDataURL(fragment) {
    let blob = new Blob([new XMLSerializer().serializeToString(fragment)], {type: 'application/xml'});
    return URL.createObjectURL(blob);
}

function doTransformation(sources) {
    sources.forEach((source) => {
        SaxonJS.transform({
            stylesheetLocation: window.stylesheets[0],
            sourceLocation: source,
        }, (result) => generateHeader(docFragmentToDataURL(result)));
    });
}

function prepareSources(stylesheets, serializedPaths) {
    window.stylesheets = stylesheets;
    doTransformation(serializedPaths);
}

initQChannel().then((channel) => {
    window.handler = channel.objects.handler;
});


