const MSG_SUCCESS = "success";
const MSG_INFO = "info";
const MSG_ERROR = "error";

function initQChannel() {
  return new Promise((resolve, reject) => {
    var channel = new QWebChannel(qt.webChannelTransport, channel => {
      if (channel) {
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
  const transform = {};
  transform.xml = new XMLSerializer().serializeToString(docFragment);
  transform.name = name;
  window.handler.transform_ready(JSON.stringify(transform));
  window.completedSources++;
  window.handler.send_message(
    "Transformation of " +
      name +
      " completed " +
      "(" +
      window.completedSources +
      "/" +
      window.sourcesCount +
      ")",
    MSG_SUCCESS
  );
  if (window.completedSources === window.sourcesCount)
    window.handler.transformations_complete(true);
}

function prepareTransformation(stylesheetIndex, params = {}) {
  return source =>
    new Promise((resolve, reject) => {
      SaxonJS.transform(
        {
          stylesheetLocation: window.stylesheets[stylesheetIndex],
          sourceLocation: source,
          stylesheetParams: params
        },
        result => {
          if (result) {
            resolve(result);
          } else {
            reject();
          }
        }
      );
    });
}

function docFragmentToObjectURL(fragment) {
  const blob = new Blob([new XMLSerializer().serializeToString(fragment)], {
    type: "application/xml"
  });
  return URL.createObjectURL(blob);
}

function getXmlId(name) {
  let n = name;
  if (name.includes("tps")) {
    n = name.substring(0, name.indexOf("tps"));
  }
  return `${window.prepend}${n}`.toLowerCase();
}

function transformSource(source) {
  return new Promise((resolve, reject) => {
    window.handler.send_message(
      "Starting transformation on " + source.name,
      MSG_INFO
    );
    const xmlId = getXmlId(source.name);
    const docxToTEI = prepareTransformation(0);
    const generateHeader = prepareTransformation(1, { xmlId });
    const addPageBreaks = prepareTransformation(2, { xmlId });
    docxToTEI(source.file)
      .then(result => generateHeader(docFragmentToObjectURL(result)))
      .then(result => addPageBreaks(docFragmentToObjectURL(result)))
      .then(result => {
        completeTransformation(source.name, result);
        resolve();
      })
      .catch(err => reject(err));
  });
}

function doTransformation(source) {
  if (window.completedSources < window.sourcesCount) {
    transformSource(source)
      .then(() => {
        doTransformation(window.sources[window.completedSources]);
      })
      .catch(error => window.handler.send_message(error, MSG_ERROR));
  }
}

function prepareSources(stylesheets, serializedPaths, options = {}) {
  window.sourcesCount = serializedPaths.length;
  window.completedSources = 0;
  window.sources = serializedPaths;
  window.stylesheets = stylesheets;
  window.prepend = options.prepend || "";
  doTransformation(window.sources[0]);
}

initQChannel().then(channel => {
  window.handler = channel.objects.handler;
});
