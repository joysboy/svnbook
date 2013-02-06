<xsl:stylesheet xmlns:xsl="http://www.w3.org/1999/XSL/Transform" version='1.0'>

  <!-- xsl:import href="http://docbook.sourceforge.net/release/xsl/current/html/docbook.xsl"/ -->
  <xsl:import href="xsl/xhtml/docbook.xsl"/>

  <xsl:include href="base-html-stylesheet.xsl"/>

  <xsl:output method="html" encoding="utf-8" indent="yes"/>

  <!-- PARAMETER REFERENCE:                                         -->
  <!-- http://docbook.sourceforge.net/release/xsl/current/doc/html/ -->

  <!-- Uncomment this to enable auto-numbering of sections -->
  <!-- xsl:param name="section.autolabel" select="1" / -->

  <!-- TOC generation settings -->
  <xsl:param name="generate.toc">
appendix  nop
article   nop
book      toc,title,figure,table,example,equation
chapter   nop
part      nop
preface   nop
qandadiv  nop
qandaset  nop
reference nop
sect1     nop
sect2     nop
sect3     nop
sect4     nop
sect5     nop
section   nop
set       nop
  </xsl:param>

</xsl:stylesheet>
