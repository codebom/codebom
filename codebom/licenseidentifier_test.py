from . import licenseidentifier as li
import io

def test_license_ngrams_matched_from_words():
    assert li._license_ngrams_matched_from_words(['a','b'], ['a','b'], 2) == (1, 1)

    # Under 90% of words, peg to 0
    assert li._license_ngrams_matched_from_words(['a','b'], ['a','b','c'], 2) == (0, 1)

    # Under 90% of filtered words, peg to 0
    assert li._license_ngrams_matched_from_words(['a','b','Z'], ['a','b','c'], 2) == (0, 1)

def test_license_ngrams_matched():
    assert li._license_ngrams_matched('a b c', 'a b c', 3) == (1, 1)
    assert li._license_ngrams_matched('a b c', 'c b a', 3) == (0, 1)
    assert li._license_ngrams_matched('a\tb c', 'a b\nc', 3) == (1, 1)
    assert li._license_ngrams_matched('a copyright holders b <b>bold move</b> c', 'a b c', 3) == (1, 1)

def test_binary_license_file(tmpdir):
    lic = tmpdir.join('LICENSE')
    data = bytearray([123, 3, 255, 0, 100])
    with io.open(lic.strpath, 'wb') as hdl:
        hdl.write(data)

    assert li.identify_license(lic.strpath, ['MIT'])[0] is None

def test_delete_template_variables():
    assert li._delete_template_variables('foo') == 'foo'
    assert li._delete_template_variables('<>') == '<>'
    assert li._delete_template_variables('<foo>') == ''
    assert li._delete_template_variables('<foo bar>') == ''

_bsd3_text = """
/*
 *  BSD LICENSE
 *
 *  Copyright(c) 2014 Broadcom Corporation.  All rights reserved.
 *
 *  Redistribution and use in source and binary forms, with or without
 *  modification, are permitted provided that the following conditions
 *  are met:
 *
 *    * Redistributions of source code must retain the above copyright
 *      notice, this list of conditions and the following disclaimer.
 *    * Redistributions in binary form must reproduce the above copyright
 *      notice, this list of conditions and the following disclaimer in
 *      the documentation and/or other materials provided with the
 *      distribution.
 *    * Neither the name of Broadcom Corporation nor the names of its
 *      contributors may be used to endorse or promote products derived
 *      from this software without specific prior written permission.
 *
 *  THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
 *  "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
 *  LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR
 *  A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT
 *  OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
 *  SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT
 *  LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE,
 *  DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY
 *  THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
 *  (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */
 """

def test_identify_license(tmpdir):
    lic = tmpdir.join('LICENSE')
    lic.write(_bsd3_text)
    assert li.identify_license(lic.strpath, ['BSD-2-Clause', 'BSD-3-Clause'])[0] == 'BSD-3-Clause'

