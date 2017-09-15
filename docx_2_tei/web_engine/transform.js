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

function addPageBreaks(name, source) {
    SaxonJS.transform({
        stylesheetLocation: window.stylesheets[2],
        sourceLocation: source,
    }, (result) => {
        let transform = {};
        transform.xml = new XMLSerializer().serializeToString(result);
        transform.name = name;
        window.handler.transform_ready(JSON.stringify(transform));
    });
}

function generateHeader(name, source) {
    SaxonJS.transform({
        stylesheetLocation: window.stylesheets[1],
        sourceLocation: source,
    }, (result) => addPageBreaks(name, docFragmentToDataURL(result)));
}

function docFragmentToDataURL(fragment) {
    let blob = new Blob([new XMLSerializer().serializeToString(fragment)], {type: 'application/xml'});
    return URL.createObjectURL(blob);
}

function doTransformation(sources) {
    sources.forEach((source) => {
        SaxonJS.transform({
            stylesheetLocation: window.stylesheets[0],
            sourceLocation: source.file,
        }, (result) => generateHeader(source.name, docFragmentToDataURL(result)));
    });
}

function prepareSources(stylesheets, serializedPaths) {
    console.log(stylesheets)
    window.stylesheets = stylesheets;
    doTransformation(serializedPaths);
}

initQChannel().then((channel) => {
    window.handler = channel.objects.handler;
});


