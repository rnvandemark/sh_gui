## An element in the chain of a doubly-linked list.
class DllNode(object):

    ## The constructor.
    #  @param self The object pointer.
    #  @param value The value associated with the node.
    def __init__(self, value):
        self.value = value
        self.parent = None
        self.child = None

## A chain of nodes that can grow and shrink, in ascending order, where a node's
#  parent will have a larger value and child will have a smaller value.
class DoublyLinkedList(object):

    ## The constructor.
    #  @param self The object pointer.
    def __init__(self):
        self.lmin = DllNode(None)
        self.lmax = DllNode(None)
        self.lmin.parent = self.lmax
        self.lmax.child = self.lmin

    ## Insert a node into the chain with the given value.
    #  @param self The object pointer.
    #  @param value The value of the node that will be added.
    #  @return The node that was created and added to the chain.
    def insert(self, value):
        node = DllNode(value)
        prev = self.lmax.child
        while prev is not None:
            if (prev == self.lmin) or (node.value >= prev.value):
                node.parent = prev.parent
                node.child = prev
                node.parent.child = node
                prev.parent = node
                break
            else:
                prev = prev.child
        return node

    ## Remove the given node from this chain. No safety checks are done, this
    #  is assumed to be in the chain and properly set, etc. This also explicitly
    #  deletes the object, even though this should be removing the only refernences
    #  to this object, but just to make sure.
    #  @param self The object pointer.
    #  @param node The Node instance to remove from the chain by adjusting the
    #  neighboring parent/child values.
    def remove(self, node):
        node.child.parent, node.parent.child = node.parent, node.child
        del node
