import cocotb

_cocotb_version_info = []
for xx in cocotb.__version__.split("."):
    try:
        _cocotb_version_info.append(int(xx))  # for strings like 'dev0'
    except ValueError:
        pass
cocotb_version_info = tuple(_cocotb_version_info)
