clean:
	rm -rf build dist lightwin.egg-info

clean-ext:
	rm -f src/lightwin/beam_calculation/cy_envelope1d/*.{c,so}
	rm -f src/lightwin/beam_calculation/integrators/*.{c,so}
	rm -f src/lightwin/core/em_fields/*.{c,so}

compile:
	python setup.py build_ext --inplace
