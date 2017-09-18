const MSG_SUCCESS = "success";
const MSG_INFO = "info";
const MSG_ERROR = "error";

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

function completeTransformation(docFragment, name) {
    let transform = {};
    transform.xml = new XMLSerializer().serializeToString(docFragment);
    transform.name = name;
    window.handler.transform_ready(JSON.stringify(transform));
    window.completedSources++;
    console.log(window.handler.MSG_SUCCESS);
    window.handler.send_message("Transformation of " + name +
    " completed " + "(" + window.completedSources + "/" + window.sourcesCount + ")", MSG_SUCCESS);
    if (window.completedSources === window.sourcesCount) window.handler.transformations_complete(true);
}

function addPageBreaks(name, source) {
    SaxonJS.transform({
        stylesheetLocation: window.stylesheets[2],
        sourceLocation: source,
    }, (result) => {
        completeTransformation(result, name);
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
    sources.forEach((source, index) => {
        window.handler.send_message("Starting transformation on " + source.name, MSG_INFO);
        SaxonJS.transform({
            stylesheetLocation: window.stylesheets[0],
            sourceLocation: source.file,
        }, (result) => generateHeader(source.name, docFragmentToDataURL(result)));
    });
}

function prepareSources(stylesheets, serializedPaths) {
    window.sourcesCount = serializedPaths.length;
    window.completedSources = 0;
    window.stylesheets = stylesheets;
    doTransformation(serializedPaths);
}

initQChannel().then((channel) => {
    window.handler = channel.objects.handler;
});


