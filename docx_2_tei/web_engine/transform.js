const MSG_SUCCESS = "success";
const MSG_INFO = "info";
const MSG_ERROR = "error";

function initQChannel() {
    return new Promise((resolve, reject) => {
        var channel = new QWebChannel(qt.webChannelTransport, (channel) => {
            if(channel) {
                resolve(channel);
            } else {
                reject();
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

function completeTransformation(name, docFragment) {
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
    return new Promise((resolve, reject) => {
        SaxonJS.transform({
            stylesheetLocation: window.stylesheets[2],
            sourceLocation: source,
        }, (result) => {
             if (result) {
                 resolve(result);
             } else {
                 reject();
             }
        });
    });
}

function generateHeader(name, source) {
    return new Promise((resolve, reject) => {
        SaxonJS.transform({
            stylesheetLocation: window.stylesheets[1],
            sourceLocation: source,
        }, (result) => {
            if (result) {
                resolve(result);
            } else {
                reject();
            }
        });
    });
}

function docFragmentToDataURL(fragment) {
    let blob = new Blob([new XMLSerializer().serializeToString(fragment)], {type: 'application/xml'});
    return URL.createObjectURL(blob);
}

function chunkSources(sources, chunkSize) {
    let all = [];
    for (let i=0; i < sources.length; i+=chunkSize) {
       all.push(sources.slice(i, i+chunkSize));
    }
    return all;
}

function transformSources(sources) {
     var tasks = sources.map((source, index) => {
        return new Promise((resolve, reject) => {
            window.handler.send_message("Starting transformation on " + source.name, MSG_INFO);
            SaxonJS.transform({
                stylesheetLocation: window.stylesheets[0],
                sourceLocation: source.file,
            }, (result) => generateHeader(source.name, docFragmentToDataURL(result)).then((result) => {
                addPageBreaks(source.name, docFragmentToDataURL(result)).then((result) => {
                    completeTransformation(source.name, result);
                    resolve();
                });
            }));
        });
    });
    return Promise.all(tasks).catch((error) => reject(error));
}

function doTransformation(sources) {
    if (window.completedBatches < window.batches.length) {
        transformSources(sources).then(() => {
            window.completedBatches++;
            doTransformation(window.batches[window.completedBatches]);
        });
    }
}

function prepareSources(stylesheets, serializedPaths) {
    window.sourcesCount = serializedPaths.length;
    window.completedSources = 0;
    window.stylesheets = stylesheets;
    window.completedBatches = 0;
    window.batches = chunkSources(serializedPaths, 5);
    doTransformation(window.batches[0]);
}

initQChannel().then((channel) => {
    window.handler = channel.objects.handler;
});


