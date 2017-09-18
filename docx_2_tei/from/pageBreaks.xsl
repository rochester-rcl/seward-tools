<?xml version="1.0" encoding="UTF-8"?>
<xsl:transform version="2.0" xmlns:xsl="http://www.w3.org/1999/XSL/Transform" xmlns="http://www.tei-c.org/ns/1.0" xpath-default-namespace="http://www.tei-c.org/ns/1.0">
    <xsl:output indent="yes" method="xml" omit-xml-declaration="no"/>
    
    <xsl:template match="@* | node()">
        <xsl:copy>
        <xsl:apply-templates select="@* | node()"/>
        </xsl:copy>
     </xsl:template>

    <xsl:template match="/TEI/text/body/ab/pb">
        <xsl:variable name="pageNumber"> <xsl:number/><xsl:value-of select="/TEI/text/body/ab/pb"/></xsl:variable>
        <pb xmlns="http://www.tei-c.org/ns/1.0">
            <xsl:attribute name="n">
                <xsl:value-of select="normalize-space($pageNumber)"/>
            </xsl:attribute>
        </pb>
    </xsl:template> 

</xsl:transform>