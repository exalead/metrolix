from metrolix.server.models import Report
from report import ReportHandler
import json

class JSONUnitReportHandler(ReportHandler):
  """Handles JSON-formatted JUnit-like reports"""

  def renderTextComparison(self, r1, r2):
    out = self.computeComparison(r1, r2)
    ret =""

    ret += "Comparison between two reports\n"
    ret += "First session: test set '%s' at %s on %s\n" % (r1.session.testset, r1.session.date, r1.session.host.name)
    ret += "Second session: test set '%s' at %s on %s\n" % (r2.session.testset, r2.session.date, r2.session.host.name)

    ret += "FIXED FAILURES\n"
    for pkg in out["fixed_failures"]:
      ret += "  In package %s\n" % pkg
      for clazz in out["fixed_failures"][pkg]:
        ret += "    In class %s\n" % clazz
        for test in out["fixed_failures"][pkg][clazz]:
          ret += "      Test: %s (error was '%s')\n" % (test, out["fixed_failures"][pkg][clazz][test])

    ret += "NEW FAILURES\n"
    for pkg in out["new_failures"]:
      ret += "  In package %s\n" % pkg
      for clazz in out["new_failures"][pkg]:
        ret += "    In class %s\n" % clazz
        for test in out["new_failures"][pkg][clazz]:
          ret += "      Test: %s (error id '%s')\n" % (test, out["new_failures"][pkg][clazz][test])
    return ret

  def renderToText(self, report):
    return "Tests report"

  def computeComparison(self, r1, r2):
    oreport = json.loads(r1.text)
    nreport = json.loads(r2.text)

    out = {}
    out["timestamp"] = nreport["timestamp"]
    out["tests_name"] = nreport["tests_name"]
    #out["root_href"] = ndir.replace("/udir/ng-build/public_html", "http://pingoo/~ng-build")

    out["fixed_failures"] = {}
    out["new_failures"] = {}

    def add(dict, a, b, c, d):
      if not dict.has_key(a):
        dict[a] = {}
      if not dict[a].has_key(b):
        dict[a][b] = {}
      dict[a][b][c] = d

    for oldfailpkg in oreport["failures"].keys():
      for oldfailclazz in oreport["failures"][oldfailpkg].keys():
        for oldfailtest in oreport["failures"][oldfailpkg][oldfailclazz].keys():
          if not nreport["failures"].has_key(oldfailpkg) or \
             not nreport["failures"][oldfailpkg].has_key(oldfailclazz) or \
             not nreport["failures"][oldfailpkg][oldfailclazz].has_key(oldfailtest):
             add(out["fixed_failures"], oldfailpkg, oldfailclazz, oldfailtest,
                 oreport["failures"][oldfailpkg][oldfailclazz][oldfailtest])

    for newfailpkg in nreport["failures"].keys():
      for newfailclazz in nreport["failures"][newfailpkg].keys():
        for newfailtest in nreport["failures"][newfailpkg][newfailclazz].keys():
          if not oreport["failures"].has_key(newfailpkg) or \
             not oreport["failures"][newfailpkg].has_key(newfailclazz) or \
             not oreport["failures"][newfailpkg][newfailclazz].has_key(newfailtest):
             add(out["new_failures"], newfailpkg, newfailclazz, newfailtest,
                 nreport["failures"][newfailpkg][newfailclazz][newfailtest])

    return out
