## DocX to TEI Desktop Transformation Tool 

### Requirements

Python3 
Pip3

### Installation

`pip install -r requirements.txt`

### Running the Application

`python3 docx_transformer.py`

### Adding Transformations

Unzip docx_2_tei/from.zip and add the .sef files to the docx_2_tei/from folder

Zip docx_2_tei/from again:

`zip -r docx_2_tei/from.zip docx_2_tei/from`

Add the file name to DocXApp.stylesheets list (See [docx_transformer.py](https://github.com/rochester-rcl/seward-tools/blob/docx-transform/docx_transformer.py#L111]))

Prepare a new transformation in web_engine/transform.js
[See the transformSource function for an example](https://github.com/rochester-rcl/seward-tools/blob/docx-transform/docx_2_tei/web_engine/transform.js#L73-L85)

transformations can be chained in the following way:
```javascript
// const source = some xml file
/*
There are 2 stylesheets in DocXApp.stylesheets, which are mapped to window.stylesheets 
*/
const transform1 = prepareTransformation(0);
const transform2 = prepareTransformation(1);
// Note subsequent results need to be in the form of an object URL in order to pass them to a transformation
transform1(source).then(docFragmentToObjectURL).then(transform2).then((result) => {
    // do something with result
    completeTransformation(source.name, result);
});
```

Re-compile resources.py (from project root)

`pyrcc5 resources.qrc -o resources.py`


