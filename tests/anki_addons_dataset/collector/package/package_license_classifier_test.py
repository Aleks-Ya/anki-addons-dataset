from typing import Optional

import pytest

from anki_addons_dataset.collector.package.package_license_classifier import PackageLicenseClassifier
from anki_addons_dataset.common.data_types import SpdxLicense


@pytest.mark.parametrize("text, expected", [
    ("                    GNU AFFERO GENERAL PUBLIC LICENSE\n                       Version 3, 19 November 2007\n"
     "13. Remote Network Interaction; Use with the GNU General Public License.", "AGPL-3.0"),
    ("                    GNU GENERAL PUBLIC LICENSE\n                       Version 3, 29 June 2007\n"
     "13. Use with the GNU Affero General Public License.", "GPL-3.0"),
    ("                    GNU GENERAL PUBLIC LICENSE\n                       Version 2, June 1991\n", "GPL-2.0"),
    ("                  GNU LESSER GENERAL PUBLIC LICENSE\n                       Version 2.1, February 1999\n"
     "This license, the Lesser General Public License, applies to ... the ordinary GNU General Public License",
     "LGPL-2.1"),
    ("                   GNU LESSER GENERAL PUBLIC LICENSE\n                       Version 3, 29 June 2007\n",
     "LGPL-3.0"),
    ("This Program is licensed under the GNU Affero General Public\nLicense v3 or later.", "AGPL-3.0"),
    ("### GNU GENERAL PUBLIC LICENSE\n\nVersion 3, 29 June 2007", "GPL-3.0"),
    ("MIT License\n\nCopyright (c) 2026 Author\n\nPermission is hereby granted, free of charge, to any person",
     "MIT"),
    ("Copyright (c) 2015 Author\n\nPermission is hereby granted, free of charge, to any person", "MIT"),
    ("                                 Apache License\n                           Version 2.0, January 2004\n",
     "Apache-2.0"),
    ("Mozilla Public License Version 2.0\n==================================\n", "MPL-2.0"),
    ("ISC License\n\nPermission to use, copy, modify, and/or distribute this software for any purpose", "ISC"),
    ("BSD 3-Clause License\n\nRedistribution and use in source and binary forms", "BSD-3-Clause"),
    ("Copyright (c) 2015, Author\nRedistribution and use in source and binary forms, with or without\n"
     "3. Neither the name of the copyright holder nor the names of its contributors", "BSD-3-Clause"),
    ("Copyright (c) 2015, Author\nRedistribution and use in source and binary forms, with or without\n",
     "BSD-2-Clause"),
    ("This is free and unencumbered software released into the public domain.", "Unlicense"),
    ("Creative Commons Legal Code\n\nCC0 1.0 Universal", "CC0-1.0"),
    ("Creative Commons Legal Code\n\nAttribution-ShareAlike 3.0 Unported", "CC-BY-SA-3.0"),
    ("Creative Commons Attribution-NonCommercial-ShareAlike 4.0 International", "CC-BY-NC-SA-4.0"),
    ("Creative Commons Attribution 4.0 International", "CC-BY-4.0"),
    ("DO WHAT THE FUCK YOU WANT TO PUBLIC LICENSE", "WTFPL"),
    ("Not quite sure what the license is yet", None),
    ("Copyright (c) 2026 Author. All rights reserved.", None),
    ("Licensed under the GNU GPL.", None),
])
def test_from_text(text: str, expected: Optional[str]):
    assert PackageLicenseClassifier.from_text(text) == expected


@pytest.mark.parametrize("source, expected", [
    ("# -*- coding: utf-8 -*-\n# SPDX-License-Identifier: AGPL-3.0-or-later\nimport aqt\n", "AGPL-3.0"),
    ("# SPDX-License-Identifier: GPL-3.0-only\n", "GPL-3.0"),
    ("# SPDX-License-Identifier: GPL-2.0+\n", "GPL-2.0"),
    ("# SPDX-License-Identifier: MIT\n", "MIT"),
    ("# Copyright: Ankitects Pty Ltd and contributors\n"
     "# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html\n", "AGPL-3.0"),
    ("# License: GNU AGPLv3 <https://www.gnu.org/licenses/agpl.html>\n", "AGPL-3.0"),
    ("# License: GNU GPL, version 3 or later; http://www.gnu.org/copyleft/gpl.html\n", "GPL-3.0"),
    ("# License: http://www.opensource.org/licenses/mit-license.php\n", "MIT"),
    ("# License: MIT\n", "MIT"),
    ("# This program is free software: you can redistribute it and/or modify\n"
     "# it under the terms of the GNU General Public License as published by\n"
     "# the Free Software Foundation, either version 3 of the License, or\n", "GPL-3.0"),
    ("# it under the terms of the GNU Affero General\n# Public License as published by\n", "AGPL-3.0"),
    ("# License: http://snmplabs.com/pyasn1/license.html\n", None),
    ("import aqt\n", None),
])
def test_from_header(source: str, expected: Optional[str]):
    assert PackageLicenseClassifier.from_header(source) == expected


def test_from_header_reads_only_the_first_lines():
    source: str = "import aqt\n" * 30 + "# License: MIT\n"

    assert PackageLicenseClassifier.from_header(source) is None


def test_from_text_returns_spdx_license():
    assert PackageLicenseClassifier.from_text("MIT License") == SpdxLicense("MIT")
