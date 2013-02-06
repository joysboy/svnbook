<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version='1.0'>

  <!-- xsl:import href="http://docbook.sourceforge.net/release/xsl/current/html/chunk.xsl"/ -->
  <xsl:import href="xsl/xhtml/chunk.xsl"/>

  <xsl:include href="base-html-stylesheet.xsl"/>

  <!-- PARAMETER REFERENCE:                                         -->
  <!-- http://docbook.sourceforge.net/release/xsl/current/doc/html/ -->

  <xsl:param name="chunker.output.encoding" select="'utf-8'"/>
  <xsl:param name="chunker.output.indent" select="'yes'"/>
  <xsl:param name="chunk.section.depth">1</xsl:param>

  <!-- Uncomment this to enable auto-numbering of sections -->
  <!-- xsl:param name="section.autolabel" select="1" / -->
  <xsl:param name="use.id.as.filename">1</xsl:param>
  <xsl:param name="chunk.first.sections">1</xsl:param>
  <xsl:param name="chunk.quietly" select="1"></xsl:param>

  <!-- TOC generation settings -->
  <xsl:param name="generate.toc">
appendix  toc,title
article   nop
book      toc,title,figure,table,example,equation
chapter   toc,title
part      toc,title
preface   toc,title
qandadiv  nop
qandaset  nop
reference toc,title
sect1     nop
sect2     nop
sect3     nop
sect4     nop
sect5     nop
section   nop
set       nop
  </xsl:param>

</xsl:stylesheet>
